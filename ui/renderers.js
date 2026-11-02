// A pre-approval slip for each SfcOutput: stamped IN POLICY or ROUTE FOR SIGN-OFF, with each code as a line.
import { h, statusPill } from "./kit/components.js";

const CODE_TEXT = {
  COST_OVER_DOMESTIC_750: "Domestic fare over $750",
  COST_OVER_INTL_1500: "International fare over $1,500",
  BOOKED_LT_14_DAYS: "Booked fewer than 14 days ahead",
  BOOKED_GT_365_DAYS: "Booked more than 365 days ahead",
  ABOVE_LOW_FARE_BAND_200: "More than $200 over the lowest logical fare",
  NON_ECONOMY_CABIN: "Cabin above economy",
  TWO_PLUS_CONNECTIONS: "Two or more connections",
};

function slip(output) {
  const codes = output.required_preauthorizations;
  const stamp = output.in_policy ? statusPill("In policy", "ok", { icon: true }) : statusPill("Route for sign-off", "warn", { icon: true });
  return h(
    "div",
    { class: "slip card" },
    h("div", { class: "slip-head row" }, h("span", { class: "slip-title", text: "Air travel pre-approval" }), stamp),
    h(
      "dl",
      { class: "slip-fields" },
      h("dt", { text: "Itinerary" }),
      h("dd", { class: "numeric", text: output.itinerary_id ?? "(audit: nothing booked)" }),
      h("dt", { text: "Reimbursable checked bags" }),
      h("dd", { text: output.reimbursable_checked_bags }),
    ),
    codes.length
      ? h("ul", { class: "slip-codes" }, codes.map((code) => h("li", {}, h("code", { text: code }), " ", h("span", { class: "muted", text: CODE_TEXT[code] ?? "" }))))
      : h("p", { class: "muted small-text", text: "No written pre-authorization needed." }),
  );
}

export default {
  SfcOutput: (output) => slip(output),
};
