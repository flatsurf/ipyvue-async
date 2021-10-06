import { Vue } from "jupyter-vue";
import Comm from "./comm";

export function activate(app, widget) {
  // Register <comm/> as a tag with Vue.js.
  Vue.component("comm", TimeSeries);
}
