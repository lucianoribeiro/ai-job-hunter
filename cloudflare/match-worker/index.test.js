import test from "node:test";
import assert from "node:assert/strict";
import worker from "./index.js";

const origin = "https://lucianoribeiro.github.io";
const env = response => ({
  MATCH_LIMITER: {limit: async () => ({success: true})},
  AI: {run: async () => ({response})},
});
const post = (path, body) => new Request(`https://worker.example${path}`, {
  method: "POST",
  headers: {origin, "content-type": "application/json"},
  body: JSON.stringify(body),
});

test("generates a CV through the route used by the dashboard", async () => {
  const generated = "PROFESSIONAL SUMMARY\n" + "Evidence-based resume content. ".repeat(8);
  const response = await worker.fetch(post("/cv", {
    profile: "QA Lead with documented test automation and team leadership experience.",
    role: "Quality Engineering Manager", language: "en", consent: true,
  }), env(generated));
  assert.equal(response.status, 200);
  assert.equal((await response.json()).cv, generated.trim());
});

test("rejects CV generation without explicit consent", async () => {
  const response = await worker.fetch(post("/cv", {
    profile: "QA Lead with enough professional profile content for validation.",
    role: "QA Lead", language: "en", consent: false,
  }), env("unused"));
  assert.equal(response.status, 400);
});

test("removes unsupported empty placeholders from model output", async () => {
  const generated = "Name: Not Available\n\nProfessional Summary:\n" + "Documented QA experience. ".repeat(6) + "\n\nEducation:\nNot Provided";
  const response = await worker.fetch(post("/cv", {
    profile: "Documented QA experience at Example Company with API testing evidence.",
    role: "QA Lead", language: "en", consent: true,
  }), env(generated));
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.doesNotMatch(body.cv, /Not Available|Not Provided|Education:/i);
});

test("keeps the existing match endpoint contract", async () => {
  const response = await worker.fetch(post("/match", {
    profile: "Senior QA engineer with Playwright and API testing experience.",
    description: "Seeking a senior QA engineer with Playwright and API testing.",
    title: "Senior QA Engineer", consent: true,
  }), env('{"score":90,"strengths":["Playwright"],"gaps":[],"recommendation":"Proceed"}'));
  assert.equal(response.status, 200);
  assert.equal((await response.json()).score, 90);
});
