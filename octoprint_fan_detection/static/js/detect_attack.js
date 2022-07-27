/*
 * View model for OctoPrint-Detect_attack
 *
 * Author: haijun si
 * License: AGPLv3
 */
$(function() {
    function Detect_attackViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        self.settings = parameters[0];
	self.control = parameters[1];
	self.loginState = parameters[2];

        self.fanSpeed = ko.observable(0);
	self.sideSR = ko.observable(0);
	self.topSR = ko.observable(0);
	self.fan_changed_status = ko.observable(0);
	self.first_attack_fan_speed = ko.observable(0);
	self.infill = ko.observable(0);
	self.layer = ko.observable(0);
	self.initial_fan_speed = ko.observable(0);
	self.initial_bad_print = ko.observable(0);
	self.initial_sideSR = ko.observable(0);
	self.initial_topSR = ko.observable(0);

	self.onDataUpdaterPluginMessage = function (plugin, data) {
		console.log(data)
		if (data.typeof == "fan_speed"){
			self.fanSpeed(data.message)
			console.log(self.fanSpeed())
		} else if (data.typeof == "sideSR") {
			self.sideSR(data.message)
		} else if (data.typeof == "topSR") {
			self.topSR(data.message)
		} else if (data.typeof == "is_fan_changed") {
			console.log( "MESSAGE:" + data.message)
			if (data.message > 0) {
				self.fan_changed_status("orange")
				var btn = document.getElementById("fan_status");
				btn.style.backgroundColor = 'orange';
			} else {
				var btn = document.getElementById("fan_status");
				btn.style.backgroundColor = 'red';
			}
		} else if (data.typeof == "first_attack" && data.message > 0) {
			self.first_attack_fan_speed(self.fanSpeed)
		} else if (data.typeof == "infill_density") {
			self.infill(data.message)
		} else if (data.typeof == "layer_height") {
			self.layer(data.message)
		} else if (data.typeof == "initial_fan_speed") {
			self.initial_fan_speed(data.message)
		} else if (data.typeof == "initial_sideSR") {
			self.initial_sideSR(data.message)
		} else if (data.typeof == "initial_topSR") {
			self.initial_topSR(data.message)
		} else if (data.typeof == "bad_initial_print" && data.message > 0) {
			console.log(data.message)
			self.initial_bad_print("True!")
			console.log(self.initial_bad_print())
		} 
				
	}
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: Detect_attackViewModel,
        dependencies: ["settingsViewModel", "controlViewModel", "loginStateViewModel"],
        // Elements to bind to, e.g. #settings_plugin_detect_attack, #tab_plugin_detect_attack, ...
        elements: [ "#settings_plugin_detect_attack", "#tab_plugin_detect_attack" ]
    });
});
