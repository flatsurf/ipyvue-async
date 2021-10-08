// Resolve when the notebook is ready to create comm targets & open comms.
async function commReady(widget_manager) {
  if (widget_manager.context) {
    // JupyterLab
    const context = widget_manager.context;
    await context.ready;

    const sessionContext = context.sessionContext;
    await sessionContext.ready;
  }
}

// Register a frontend comma target in this notebook and return a promise
// that resolves to the comm once the backend has connected to it.
function registerCommTarget(widget_manager, target, callback) {
  if (widget_manager.context) {
    // JupyterLab
    const context = widget_manager.context;
    const sessionContext = context.sessionContext;
    const kernel = sessionContext.session.kernel;

    return new Promise((accept) => {
      kernel.registerCommTarget(target, (comm) => {
        comm.onMsg = callback;
        accept(comm);
      });
    });
  } else {
    // Classic Notebook
    return new Promise((accept) => {
      widget_manager.comm_manager.register_target(target, (comm) => {
        comm.on_msg(callback);
        accept(comm);
      });
    });
  }
}

// Return a comm to the backend.
function createComm(widget_manager, target) {
  if (widget_manager.context) {
    // JupyterLab
    const context = widget_manager.context;
    const sessionContext = context.sessionContext;
    const kernel = sessionContext.session.kernel;

    return kernel.createComm(target);
  } else {
    // Classic Notebook
    return widget_manager.comm_manager.new_comm(target, {});
  }
}

export default {
  // This object is provided by ipyvue's VueView
  inject: [ 'viewCtx' ],
  template: `
    <div>
      <slot />
    </div>
  `,
  async mounted() {
    const view = this.viewCtx.getView();
    const model = view.model;
    const target = `${model.attributes.target}-${view.cid}`;
    await commReady(model.widget_manager);

    // Create a comm target that the backend can send data to.
    const commTarget = registerCommTarget(model.widget_manager, target, (msg) => this.onMessage(msg));

    // We tell the backend about our comm target.
    const toCommWidget = createComm(model.widget_manager, model.attributes.target);
    toCommWidget.open();
    toCommWidget.send({command: "register", target});

    // Wait for the backend to connect to our comm target.
    this.comm = await commTarget;
  },
  data() {
    return {
      comm: null,
      tokens: {},
    };
  },
  props: ['refs'],
  methods: {
    onMessage(message) {
      const payload = message.content.data;
      const action = payload.action;
      if (action === "call") {
        const {target, endpoint, args} = payload.data;
        this.call(target, endpoint, args)
      } else if (action === "cancel") {
        const { identifier } = payload.data;
        this.cancel(identifier);
      } else if (action === "query") {
        const {identifier, data} = payload.data;
        const {target, endpoint, args} = data;
        this.query(identifier, target, endpoint, args);
      } else {
        throw new Error(`Unsupported action ${action}`);
      }
    },

    call(target, endpoint, args) {
      const ref = this.refs[target];
      ref[endpoint](...args);
    },

    async query(identifier, target, endpoint, args) {
      const ref = this.refs[target];
      // TODO: Exception handling.
      // TODO: Await if promise.
      let value = ref[endpoint]
      if (typeof value === "function")
        value = value(...args)
      // TODO: else if (args) complain.
      if (typeof value.then === "function") {
        if (value.cancel != null)
          // TODO: Cleanup
          this.tokens[identifier] = () => value.cancel();
        value = await value;
      }
      this.comm.send({command: "callback", data: { value, identifier }});
    },

    cancel(identifier) {
      const token = this.tokens[identifier];
      if (token === undefined) {
        console.log(`Cannot cancel request ${identifier}. No cancellation defined for this request.`)
        return;
      }
      token();
    }
  }
}
