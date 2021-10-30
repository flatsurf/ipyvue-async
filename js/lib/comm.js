/* ******************************************************************************
 * Copyright (c) 2021 Julian Rüth <julian.rueth@fsfe.org>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * *****************************************************************************/

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

// Return whether object is a promise.
function isPromise(object) {
  return typeof(object) === "object" && typeof(object.then) === "function";
}

export default {
  // This object is provided by ipyvue's VueView
  inject: [ 'viewCtx' ],
  template: `
    <div>
      <slot />
      <slot name="errors" v-bind:errors="errors">
        <!--
          Styling of error messages derived from Bootstrap, licensed under The MIT License (MIT):

          Copyright (c) 2011-2018 Twitter, Inc.
          Copyright (c) 2011-2018 The Bootstrap Authors

          Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

          The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

          THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
        -->
        <div style="color: #a94442; background-color: #f2dede; border: 1px solid #ebccd1; padding: 15px; padding-right: 35px; border-radius: 4px; margin-top: 10px;" v-for="(error, i) of errors" :key="i">
          {{ error }}
          <button style="position: relative; top: -2px; right: -21px; color: inherit; padding: 0; cursor: pointer; float: right; opacity: .2; font-size: 21px; border: 0; background: 0 0;" @click="errors.splice(i, 1)">×</button>
        </div>
      </slot>
    </div>
  `,
  async mounted() {
    const view = this.viewCtx.getView();
    const model = view.model;
    const target = `${model.attributes.target}-${[...Array(8)].map(() => Math.random().toString(36)[2]).join('')}`;
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
      errors: [],
    };
  },
  props: ['refs'],
  methods: {
    onMessage(message) {
      try {
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
          void this.query(identifier, target, endpoint, args);
        } else {
          throw new Error(`Unsupported action ${action}.`);
        }
      } catch (e) {
        this.errors.push(e.message);
        throw e;
      }
    },

    endpoint(target, method) {
      const ref = this.refs[target];
      if (ref == null)
        throw new Error(`No ref="${target}" found in component.`);
      const endpoint = ref[method];
      if (endpoint == null)
        throw new Error(`No function ${method} found in component ${target}.`)
      const bound = endpoint.bind ? endpoint.bind(ref) : endpoint;
      return bound;
    },

    call(target, endpoint, args) {
      const value = this.endpoint(target, endpoint)(...args);
      if (isPromise(value)) {
        value.then(() => {}, (e) => {
          this.errors.push(e.message);
          throw e;
        });
      }
    },

    async query(identifier, target, endpoint, args) {
      try {
        let value = null;
        try {
          value = this.endpoint(target, endpoint);
          if (typeof value === "function")
            value = value(...args)
          else if (args.length)
            throw Error(`Cannot call ${target}.${endpoint} with arguments since it is not a function.`);
          if (isPromise(value)) {
            if (value.cancel != null)
              this.tokens[identifier] = () => value.cancel();
            else
              this.tokens[identifier] = () => {};
            value = await value;
          }
        } catch (e) {
          this.comm.send({command: "callback", data: { error: e.message, identifier }});
          return;
        }
        this.comm.send({command: "callback", data: { value, identifier }});
      } finally {
        if (this.tokens[identifier])
          delete this.tokens[identifier];
      }
    },

    cancel(identifier) {
      const token = this.tokens[identifier];
      if (token === undefined) {
        this.errors.push(`Cannot cancel request ${identifier}. No cancellation for this request available anymore.`);
        return;
      }
      token();
    }
  }
}
