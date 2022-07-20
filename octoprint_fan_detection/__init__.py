# coding=utf-8
from __future__ import absolute_import

import os, re, time, requests, flask
import pandas as pd
import numpy as np
import tflite_runtime.interpreter as tflite
import octoprint.plugin, octoprint.filemanager, octoprint.filemanager.util, octoprint.util, octoprint.events



class Detect_attackPlugin(octoprint.plugin.StartupPlugin,
                          octoprint.plugin.EventHandlerPlugin,
                          octoprint.plugin.SettingsPlugin,
                          octoprint.plugin.AssetPlugin,
                          octoprint.plugin.TemplatePlugin):
    
    sideModel = '/home/pi/nnside_model.tflite'
    topModel = '/home/pi/nntop_model.tflite'
    sideCluster = pd.read_csv('/home/pi/side_min_cluster.csv')
    topCluster = pd.read_csv('/home/pi/top_min_cluster.csv')
    # max best quality SR plus the MAE
    sideMAE = .466
    topMAE = 1.69
    sideMax = sideCluster['side'].max() + sideMAE
    topMax = topCluster['top/bottom'].max() + topMAE
    print(sideMax)
    print(topMax)
    fan_speed_pattern = re.compile("^M106.* S(\d+\.?\d*).*")
    fan_speed = 100
    fan_speed_actual = 0
    minFAN = 0
    maxFAN = 0
    infill = 0
    layer_H = 0
    initial_sideSR = 0
    initial_topSR = 0
    ##~~ SettingsPlugin mixin
    def on_after_startup(self):
        self._logger.info("Plugin Started")
        self.update_fan_speed()
        return
            
    def get_settings_defaults(self):
        return {
            # default settings
        }

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
    
    def process_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if not gcode:
            print("NOT GCODE")
            return
        elif gcode in ("M106") and self.printing:
            matched = self.fan_speed_pattern.match(cmd.upper())
            if matched:
                new_fan_speed = float(matched.group(1))  * 100.0 / 255.0
                fan_speed_actual = 255
                print(new_fan_speed)
                print(self.fan_speed)
                # note if the initial print is good or not, if it was already bad then just
                # compare the new predicted sr to the initial print + MAE, but if it was good then
                # just compare it to the maxes
                sideSR = self.predict_SR(self.layer_H, self.infill, new_fan_speed, self.sideModel)
                topSR = self.predict_SR(self.layer_H, self.infill, new_fan_speed, self.topModel)
                is_fan_changed = self.predict_print_quality(sideSR, topSR)
                cmd = "M106 S"
                if is_fan_changed:
                    # there is an attempted attack, change green button to orange
                    fan_speed_actual = float(matched.group(1)) * 255.0 / 100.0
                    self.fan_speed = new_fan_speed
                    self.update_fan_speed()
                    self.update_surface_roughness(sideSR, topSR)
                # there is now a declared attack, change green button to red
                cmd += str(fan_speed_actual)
                self.send_attack_message(is_fan_changed, self.first_attack)
                if self.first_attack:
                    self.first_attack = False
                return cmd
        else:
            return
                
##    def gcode_received_hook(self, comm, line, *args, **kwargs):
        # get fan speed when printing from sd card
##        print(line)
##        if "M106" not in line:
##            return line
##        
##        matched = self.fan_speed_pattern.match(line)
##        if matched:
##            self.fan_speed = float(matched.group(1)) * 100.0 / 255.0 #get percent
##            msg = dict(
##                fanSpeed=str(self.fan_speed)
##            )
##            self._plugin_manager.send_plugin_message(self._identifier, msg)
##
##        return line
    def send_Message(self, typeof, message):
        payload = {"typeof": typeof, "message" : message}
        self._plugin_manager.send_plugin_message(self._identifier, payload)
                                                 
    def send_attack_message(self, is_fan_changed, first_attack = False):
            self.send_Message("is_fan_changed", is_fan_changed)
            self.send_Message("first_attack", int(first_attack))

            
    def update_surface_roughness(self, sideSR, topSR, initial_update = 0):
        self.send_Message("sideSR", sideSR)
        self.send_Message("topSR", topSR)
        if initial_update:
            self.send_Message("initial_sideSR", self.initial_sideSR)
            self.send_Message("initial_topSR", self.initial_topSR)
        
    def update_fan_speed(self):
        self.send_Message("fan_speed", self.fan_speed)

    def on_event(self, event, payload):
        print(event)
        if event == octoprint.events.Events.STARTUP:
            self._logger.info("Octoprint Started")
            # TESTING
            x = self.predict_SR(.3, 50, 0, self.sideModel)
            y = self.predict_SR(.3, 50, 100, self.sideModel)
            z = self.predict_SR(.3, 50, 50, self.sideModel)
        elif event == octoprint.events.Events.PRINT_STARTED:
            self.printing = True
            self.bad_initial_print = False
            self.first_attack = True
            filename = payload["path"]
            x = filename.split("/DATA/")
            print(x)
            file = "/home/pi/Downloads/haijun/data/" + x[1]
            self.minFAN, self.fan_speed, self.infill, self.layer_H = self.readGCode(file)
            self.initial_sideSR = self.predict_SR(self.layer_H, self.infill, self.fan_speed, self.sideModel)
            self.initial_topSR = self.predict_SR(self.layer_H, self.infill, self.fan_speed, self.topModel)
            # send messages
            print(self.initial_sideSR)
            print(type(self.initial_topSR))
            self.send_Message("infill_density", self.infill)
            self.send_Message("layer_height", self.layer_H)
            self.send_Message("initial_fan_speed", self.fan_speed)
            self.update_surface_roughness(self.initial_sideSR, self.initial_topSR, 1)
            self.bad_initial_print = self.predict_print_quality(self.initial_sideSR, self.initial_topSR)
            print(self.bad_initial_print)
            self.send_Message("bad_initial_print", int(self.bad_initial_print))
        elif event == octoprint.events.Events.CLIENT_AUTHED:
            self.update_fan_speed()
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
        print("SIDE SR PREDICTION IS : ", sideSR)
        print("TOP SR PREDICTION IS : ", topSR)
        # low tolerance here
        if self.bad_initial_print == True:
            print(" BAD INITIAL PRINT SETTINGS BUT ALSO BAD FAN SPEED")
            return ((sideSR > self.initial_sideSR + self.sideMAE) or
                                (topSR > self.initial_topSR + self.topMAE))
        else:
            print("testing high tolerance")
            return self.predict_print_quality_against_high_tolerance(sideSR, topSR)
    
    def createFilePreProcessor(self, path, file_object, blinks=None, printer_profile=None, allow_overwrite=True, *args, **kwargs):

        fileName = file_object.filename
        if not octoprint.filemanager.valid_file_type(fileName, type="gcode"):
            return file_object
        fileStream = file_object.stream()
        self._logger.info("GcodePreProcessor started processing.")
        self.gcode_preprocessors[path] = GcodePreProcessor(fileStream, self.layer_indicator_patterns, self.layer_move_pattern, self.filament_change_pattern, self.python_version, self._logger)
        return octoprint.filemanager.util.StreamWrapper(fileName, self.gcode_preprocessors[path])
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
__plugin_name__ = "Detect Attack"


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
##        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.gcode_received_hook,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.process_gcode
##        "octoprint.filemanager.preprocessor": __plugin_implementation__.createFilePreProcessor
    }
    global __plugin_settings_overlay__
    __plugin_settings_overlay__ = dict(appearance=dict(components=dict(order=dict(tab=["Detect_Attack"]))))

