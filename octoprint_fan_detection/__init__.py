# coding=utf-8
from __future__ import absolute_import

import re
import pandas as pd
import numpy as np
import tflite_runtime.interpreter as tflite
import octoprint.plugin, octoprint.filemanager, octoprint.filemanager.util, octoprint.util, octoprint.events


class Detect_attackPlugin(octoprint.plugin.StartupPlugin,
                          octoprint.plugin.EventHandlerPlugin,
                          octoprint.plugin.SettingsPlugin,
                          octoprint.plugin.AssetPlugin,
                          octoprint.plugin.TemplatePlugin):
    
    # Class Variables
    sideModel = 'https://github.com/haijun12/OctoPrint-fan_Detection/models/nnside_model.tflite'
    topModel = 'https://github.com/haijun12/OctoPrint-fan_Detection/models/nntop_model.tflite'
    sideCluster = pd.read_csv('https://github.com/haijun12/OctoPrint-fan_Detection/data/side_min_cluster.csv')
    topCluster = pd.read_csv('https://github.com/haijun12/OctoPrint-fan_Detection/data/top_min_cluster.csv')
    # max best quality SR plus the MAE
    sideMAE = .466
    topMAE = 1.69
    sideMax = sideCluster['side'].max() + sideMAE
    topMax = topCluster['top/bottom'].max() + topMAE
    fan_speed_pattern = re.compile("^M106.* S(\d+\.?\d*).*")
    fan_speed_actual = 0
    fan_speed = 0
    minFAN = 0
    infill = 0
    layer_H = 0
    initial_sideSR = 0
    initial_topSR = 0
    MAX_FAN_SPEED = 255
    MAX_FAN_SPEED_PERCENT = 100.0

    
    def process_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        """
        Only observes Fan Speed GCode M106, does not look for M107

        This conducts all the backend features of predicting new fan speed, 
        updating it only if the print quality is not affected poorly. 
        """
        if not gcode:
            return
        elif gcode in ("M106") and self.printing:
            matched = self.fan_speed_pattern.match(cmd.upper())
            if matched:
                new_fan_speed = float(matched.group(1))  * self.MAX_FAN_SPEED_PERCENT / self.MAX_FAN_SPEED
                fan_speed_actual = fan_speed
                # note if the initial print is good or not, if it was already bad then just
                # compare the new predicted sr to the initial print + MAE, but if it was good then
                # just compare it to the maxes
                sideSR = self.predict_SR(self.layer_H, self.infill, new_fan_speed, self.sideModel)
                topSR = self.predict_SR(self.layer_H, self.infill, new_fan_speed, self.topModel)
                bad_fs_effect = self.predict_print_quality(sideSR, topSR)
                # GCode Command to change fan speed
                cmd = "M106 S"
                if not bad_fs_effect:
                    # there is an attempted attack, change green button to orange
                    fan_speed_actual = float(matched.group(1)) * self.MAX_FAN_SPEED / self.MAX_FAN_SPEED_PERCENT
                    self.fan_speed = new_fan_speed
                    self.update_fan_speed()
                    self.update_surface_roughness(sideSR, topSR)
                # there is now a declared attack, change green button to red
                cmd += str(fan_speed_actual)
                self.send_attack_message(bad_fs_effect, self.first_attack)
                if self.first_attack: self.first_attack = False
                return cmd

    def on_event(self, event, payload):
        """
        Events to read initial printing parameters along with cleaning up 
        potential memory leaks
        """
        if event == octoprint.events.Events.STARTUP:
            self._logger.info("Octoprint Started")
            # TESTING
            # x = self.predict_SR(.15, 50, 0, self.sideModel)
            # y = self.predict_SR(.15, 50, 100, self.sideModel)
            # z = self.predict_SR(.15, 50, 50, self.sideModel)
            # a = self.predict_SR(.15, 50, 0, self.topModel)
            # b = self.predict_SR(.15, 50, 100, self.topModel)
            # c = self.predict_SR(.15, 50, 50, self.topModel)
            # print(x,y,z)
            # print(a,b,c)
        elif event == octoprint.events.Events.PRINT_STARTED:
            self.printing = True
            self.bad_initial_print = False
            self.first_attack = True
            filename = payload["path"]
            file = "/home/pi/Downloads/" + filename
            self.minFAN, self.fan_speed, self.infill, self.layer_H = self.readGCode(file)
            self.initial_sideSR = self.predict_SR(self.layer_H, self.infill, self.fan_speed, self.sideModel)
            self.initial_topSR = self.predict_SR(self.layer_H, self.infill, self.fan_speed, self.topModel)
            # send messages
            self.update_fan_speed()
            self.send_Message("infill_density", self.infill)
            self.send_Message("layer_height", self.layer_H)
            self.send_Message("initial_fan_speed", self.fan_speed)
            self.update_surface_roughness(self.initial_sideSR, self.initial_topSR, 1)
            self.bad_initial_print = self.predict_print_quality(self.initial_sideSR, self.initial_topSR)
            self.send_Message("bad_initial_print", int(self.bad_initial_print))
        elif event == octoprint.events.Events.PRINT_CANCELLED or event == octoprint.events.Events.PRINT_DONE:
            # Stop Process GCode Fan Trigger
            self.printing = False
        else:
            return

    # HELPER FUNCTIONS

    def readGCode(self, file):
        with open(str(file), 'r') as f:
            for line_text in f.readlines():
                line = str(line_text)
                if line.startswith("; min_fan_speed = "):
                    x = line.split("=")
                    y = x[1].split("\n")
                    minFAN_SPEED = y[0]
                if line.startswith("; max_fan_speed = "):
                    x = line.split("=")
                    y = x[1].split("\n")
                    maxFAN_SPEED = y[0]
                if line.startswith("; fill_density = "):
                    x = line.split("=")
                    y = x[1].split("%\n")
                    fill_DENSITY = y[0]
                if line.startswith("; layer_height = "):
                    x = line.split("=")
                    y = x[1].split("\n")
                    layer_H = y[0]
        return minFAN_SPEED, maxFAN_SPEED, fill_DENSITY, layer_H

                    
    def predict_SR(self, lt, ld, fs, model):
        # Load TFLite model and allocate tensors.
        interpreter = tflite.Interpreter(model)
        interpreter.allocate_tensors()
        # Get input and output tensors.
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        # Convert features to NumPy array
        params = [lt, ld, fs]
        np_features = np.array(params)
        # If the expected input type is int8 (quantized model), rescale data
        input_type = input_details[0]['dtype']

        # Convert features to NumPy array of expected type
        np_features = np_features.astype(input_type)

        # Add dimension to input sample (TFLite model expects (# samples, data))
        np_features = np.expand_dims(np_features, axis=0)

        # Create input tensor out of raw features
        interpreter.set_tensor(input_details[0]['index'], np_features)
        interpreter.invoke()
        prediction = interpreter.get_tensor(output_details[0]['index'])
        prediction = float(prediction[0][0])
        rounded_result = round(prediction, 4)
        return rounded_result #round it

    # returns true if the print quality is bad
    def predict_print_quality_against_high_tolerance(self, sideSR, topSR):
        return (sideSR > self.sideMax or topSR > self.topMax)
    
    def predict_print_quality(self, sideSR, topSR):
        if self.bad_initial_print == True:
            # High Tolerance
            return ((sideSR > self.initial_sideSR + self.sideMAE) or
                                (topSR > self.initial_topSR + self.topMAE))
        else:
            # Low Tolerance
            return self.predict_print_quality_against_high_tolerance(sideSR, topSR)
    
    def send_Message(self, typeof, message):
        payload = {"typeof": typeof, "message" : message}
        self._plugin_manager.send_plugin_message(self._identifier, payload)
                                                 
    def send_attack_message(self, is_fan_bad, first_attack = False):
            self.send_Message("is_fan_bad", int(is_fan_bad))
            self.send_Message("first_attack", int(first_attack))

            
    def update_surface_roughness(self, sideSR, topSR, initial_update = 0):
        self.send_Message("sideSR", sideSR)
        self.send_Message("topSR", topSR)
        if initial_update:
            self.send_Message("initial_sideSR", self.initial_sideSR)
            self.send_Message("initial_topSR", self.initial_topSR)
        
    def update_fan_speed(self):
        self.send_Message("fan_speed", self.fan_speed)

    ##~~ AssetPlugin mixin    
    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/detect_attack.js"],
            "css": ["css/detect_attack.css"],
            "less": ["less/detect_attack.less"]
        }
    def get_template_configs(self):
        return [
            dict(type="tab", custom_bindings=True)
            ]
    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "detect_attack": {
                "displayName": "Detect_attack Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "haijun12",
                "repo": "OctoPrint-Detect_attack",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/haijun12/OctoPrint-Detect_attack/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "FSAD"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Detect_attackPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.process_gcode
    }
    global __plugin_settings_overlay__
    __plugin_settings_overlay__ = dict(appearance=dict(components=dict(order=dict(tab=["Detect_Attack"]))))
