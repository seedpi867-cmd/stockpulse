import { proxyTo } from "./proxy.js";
export default (req, res) => proxyTo(req, res, "/api/journal");
