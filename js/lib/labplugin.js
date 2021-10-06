const plugin = require('./plugin');
const base = require('@jupyter-widgets/base');

module.exports = {
  id: 'ipyvue-comm:plugin',
  requires: [base.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      plugin.activate(app, widgets);
      widgets.registerWidget({
          name: 'ipyvue-comm',
          version: plugin.version,
          exports: plugin
      });
  },
  autoStart: true
};
