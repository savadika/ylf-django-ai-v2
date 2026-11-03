"""Render a static, human-readable engineering cockpit."""

from __future__ import annotations

from datetime import datetime
from html import escape
import json
from pathlib import Path
import re
from typing import Any

from .api_scope import CORE_API_GROUPS, api_contract_count
from .specs import SpecRecord, load_specs


CSS = """
:root {
  color-scheme: light;
  --ink: #172033;
  --ink-strong: #0d1526;
  --muted: #667085;
  --muted-light: #98a2b3;
  --line: #dfe4eb;
  --line-strong: #cfd6e0;
  --panel: #ffffff;
  --canvas: #f3f5f8;
  --night: #0b1220;
  --night-raised: #121d31;
  --blue: #1d64d8;
  --blue-soft: #eaf2ff;
  --green: #087a55;
  --green-soft: #e7f7f0;
  --amber: #9a5b00;
  --amber-soft: #fff4dc;
  --red: #b42318;
  --red-soft: #fdecea;
  --neutral-soft: #eef2f6;
  --shadow: 0 18px 48px rgba(20, 32, 52, .07);
  --shadow-soft: 0 8px 24px rgba(20, 32, 52, .05);
  --radius: 18px;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  min-width: 320px;
  color: var(--ink);
  background:
    radial-gradient(circle at 92% 5%, rgba(46, 111, 220, .12), transparent 27rem),
    linear-gradient(180deg, #f8f9fb 0, var(--canvas) 28rem),
    var(--canvas);
  font-family: "Segoe UI Variable", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.skip-link {
  position: fixed; left: 18px; top: 10px; z-index: 100; padding: 10px 14px;
  color: var(--night); background: #fff; border-radius: 9px;
  transform: translateY(-150%); transition: transform .18s ease;
}
.skip-link:focus { transform: translateY(0); }
.topbar {
  position: relative; color: #fff; background:
    radial-gradient(circle at 88% -30%, rgba(66, 133, 244, .34), transparent 25rem),
    linear-gradient(120deg, #0a111e, #111f35 58%, #101a2d);
  border-bottom: 1px solid rgba(255, 255, 255, .08);
}
.topbar::after {
  content: ""; position: absolute; inset: auto 0 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(86, 154, 255, .85), transparent);
}
.topbar-inner {
  width: min(1280px, calc(100% - 40px)); min-height: 74px; margin: 0 auto;
  display: flex; align-items: center; gap: 24px;
}
.brand {
  display: inline-flex; align-items: center; gap: 12px; min-width: 0;
  color: #fff; text-decoration: none;
}
.brand:hover { text-decoration: none; }
.brand-mark {
  position: relative; width: 38px; height: 38px; flex: 0 0 38px;
  border: 1px solid rgba(255, 255, 255, .2); border-radius: 12px;
  background: linear-gradient(145deg, rgba(54, 126, 241, .95), rgba(29, 74, 148, .9));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .25), 0 8px 20px rgba(0, 0, 0, .2);
}
.brand-mark::before, .brand-mark::after {
  content: ""; position: absolute; left: 9px; right: 9px; height: 3px;
  border-radius: 99px; background: rgba(255, 255, 255, .95);
}
.brand-mark::before { top: 12px; box-shadow: 0 7px 0 rgba(255, 255, 255, .55); }
.brand-mark::after { width: 12px; right: auto; bottom: 7px; opacity: .75; }
.brand-copy { display: grid; line-height: 1.2; }
.brand-copy strong { font-size: .9rem; letter-spacing: .12em; }
.brand-copy span { color: #aebdd3; font-size: .73rem; letter-spacing: .04em; }
.topbar-context {
  display: flex; align-items: center; gap: 8px; margin-left: auto;
  color: #b5c1d3; font-size: .75rem; letter-spacing: .07em; white-space: nowrap;
}
.context-dot {
  width: 7px; height: 7px; border-radius: 50%; background: #61d4a3;
  box-shadow: 0 0 0 4px rgba(97, 212, 163, .12);
}
.top-nav { display: flex; align-items: center; gap: 4px; padding-left: 10px; }
.top-nav a {
  display: inline-flex; align-items: center; min-height: 38px; padding: 0 12px;
  color: #c8d2e1; border-radius: 9px; font-size: .84rem; text-decoration: none;
}
.top-nav a:hover, .top-nav a:focus-visible {
  color: #fff; background: rgba(255, 255, 255, .08); text-decoration: none;
}
main {
  width: min(1280px, calc(100% - 40px)); margin: 0 auto; padding: 30px 0 44px;
}
h1, h2, h3, p { margin-top: 0; }
.hero {
  position: relative; display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(300px, .65fr);
  gap: 32px; align-items: stretch; padding: 32px; overflow: hidden;
  color: #fff; border: 1px solid rgba(255, 255, 255, .08); border-radius: 24px;
  background:
    linear-gradient(125deg, rgba(255, 255, 255, .035), transparent 48%),
    linear-gradient(135deg, #111c30, #172a46);
  box-shadow: 0 24px 56px rgba(12, 23, 41, .16);
}
.hero::before {
  content: ""; position: absolute; width: 420px; height: 420px; right: -170px; top: -250px;
  border: 1px solid rgba(117, 169, 255, .18); border-radius: 50%;
  box-shadow: 0 0 0 58px rgba(58, 119, 219, .05), 0 0 0 118px rgba(58, 119, 219, .035);
  pointer-events: none;
}
.hero-copy { position: relative; z-index: 1; align-self: center; }
.eyebrow {
  display: inline-flex; align-items: center; gap: 8px; color: #9fc0ff;
  font-size: .73rem; font-weight: 750; letter-spacing: .14em; text-transform: uppercase;
}
.eyebrow::before { content: ""; width: 18px; height: 2px; background: #5b9cff; border-radius: 99px; }
.hero h1 {
  max-width: 760px; margin: 11px 0 12px; color: #fff;
  font-size: clamp(2.15rem, 4.5vw, 4.2rem); line-height: 1.06; letter-spacing: -.055em;
}
.hero h1 span { color: #8db6ff; }
.hero-copy > p {
  max-width: 650px; margin: 0; color: #aebdd3; font-size: 1rem;
}
.hero-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 20px; }
.hero-chip {
  display: inline-flex; align-items: center; gap: 7px; min-height: 30px; padding: 4px 10px;
  color: #c4d0e1; background: rgba(255, 255, 255, .06);
  border: 1px solid rgba(255, 255, 255, .1); border-radius: 8px; font-size: .76rem;
}
.hero-chip::before {
  content: ""; width: 5px; height: 5px; border-radius: 50%; background: #6ea8ff;
}
.status-spotlight {
  --spot: #98a2b3; --spot-soft: rgba(152, 162, 179, .12);
  position: relative; z-index: 1; display: grid; grid-template-columns: auto 1fr;
  gap: 16px; align-content: center; min-width: 0; padding: 24px;
  border: 1px solid rgba(255, 255, 255, .13); border-radius: 18px;
  background: rgba(255, 255, 255, .055); backdrop-filter: blur(10px);
}
.status-spotlight.status-passed { --spot: #59d6a4; --spot-soft: rgba(89, 214, 164, .12); }
.status-spotlight.status-partial { --spot: #ffc15c; --spot-soft: rgba(255, 193, 92, .12); }
.status-spotlight.status-failed { --spot: #ff7d86; --spot-soft: rgba(255, 125, 134, .12); }
.status-orb {
  position: relative; width: 54px; height: 54px; flex: 0 0 54px; border-radius: 16px;
  background: var(--spot-soft); border: 1px solid color-mix(in srgb, var(--spot) 35%, transparent);
}
.status-orb::before {
  content: ""; position: absolute; inset: 10px; border: 2px solid var(--spot);
  border-radius: 50%; box-shadow: 0 0 18px var(--spot-soft);
}
.status-orb::after {
  content: "✓"; position: absolute; inset: 0; display: grid; place-items: center;
  color: var(--spot); font-family: "Segoe UI Symbol", "Arial Unicode MS", sans-serif;
  font-size: 1.42rem; font-weight: 800; line-height: 1;
}
.status-spotlight.status-failed .status-orb::after,
.status-spotlight.status-partial .status-orb::after {
  content: "!";
}
.status-spotlight.status-unverified .status-orb::after {
  content: "?";
}
.status-caption { margin-bottom: 6px; color: #9fb0c7; font-size: .74rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
.status-spotlight strong { display: block; color: #fff; font-size: 1.55rem; line-height: 1.2; letter-spacing: -.025em; }
.status-spotlight small { display: block; margin-top: 5px; color: #aebdd3; font-size: .79rem; }
.muted { color: var(--muted); }
.metrics {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px;
  margin: 18px 0;
}
.metric-card, .panel {
  background: rgba(255, 255, 255, .94); border: 1px solid var(--line);
  border-radius: var(--radius); box-shadow: var(--shadow-soft);
}
.metric-card {
  position: relative; min-width: 0; padding: 19px 19px 17px; overflow: hidden;
}
.metric-card::before {
  content: ""; position: absolute; inset: 0 auto 0 0; width: 3px;
  background: linear-gradient(180deg, #4b8cf2, rgba(75, 140, 242, .08));
}
.metric-card.metric-passed::before { background: linear-gradient(180deg, #22a878, rgba(34, 168, 120, .08)); }
.metric-card.metric-failed::before { background: linear-gradient(180deg, #d94851, rgba(217, 72, 81, .08)); }
.metric-card.metric-partial::before { background: linear-gradient(180deg, #d58a19, rgba(213, 138, 25, .08)); }
.metric-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 15px; }
.metric-label { color: var(--muted); font-size: .76rem; font-weight: 650; letter-spacing: .035em; }
.metric-mark {
  display: grid; place-items: center; width: 28px; height: 28px; flex: 0 0 28px;
  color: var(--blue); background: var(--blue-soft); border-radius: 8px;
  font-size: .67rem; font-weight: 800; letter-spacing: .04em;
}
.metric-passed .metric-mark { color: var(--green); background: var(--green-soft); }
.metric-failed .metric-mark { color: var(--red); background: var(--red-soft); }
.metric-partial .metric-mark { color: var(--amber); background: var(--amber-soft); }
.metric-value {
  display: flex; align-items: baseline; flex-wrap: wrap; gap: 5px;
  min-height: 38px; color: var(--ink-strong); font-size: 1.72rem;
  font-weight: 780; line-height: 1.15; letter-spacing: -.035em;
}
.metric-value .unit { color: var(--muted); font-size: .88rem; font-weight: 600; letter-spacing: 0; }
.metric-caption { margin: 7px 0 0; color: var(--muted); font-size: .74rem; }
.metric-progress {
  height: 5px; margin-top: 14px; overflow: hidden; background: #edf0f5; border-radius: 99px;
}
.metric-progress > span { display: block; height: 100%; background: linear-gradient(90deg, #347ee8, #69a7ff); border-radius: inherit; }
.coverage-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 4px; }
.coverage-item { min-width: 0; padding: 8px 10px; background: #f7f9fc; border: 1px solid #e7ebf1; border-radius: 10px; }
.coverage-item span { display: block; color: var(--muted); font-size: .68rem; }
.coverage-item strong { display: block; margin-top: 1px; color: var(--ink); font-size: 1.08rem; line-height: 1.3; }
.regression-panel {
  margin: 0 0 18px; padding: 22px;
  background:
    radial-gradient(circle at 94% 0, rgba(46, 111, 220, .09), transparent 20rem),
    rgba(255, 255, 255, .96);
}
.regression-layout {
  display: flex; align-items: center; justify-content: space-between; gap: 28px;
}
.regression-copy { min-width: 0; }
.regression-copy h2 { margin: 0; color: var(--ink-strong); font-size: 1.3rem; letter-spacing: -.025em; }
.regression-copy p { max-width: 680px; margin: 6px 0 0; color: var(--muted); font-size: .84rem; }
.regression-chips { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 12px; }
.regression-chip {
  display: inline-flex; align-items: center; gap: 6px; min-height: 27px; padding: 3px 9px;
  color: #46546a; background: #f5f8fc; border: 1px solid #e2e8f0;
  border-radius: 7px; font-size: .7rem;
}
.regression-chip::before { content: ""; width: 5px; height: 5px; border-radius: 50%; background: #4b8cf2; }
.regression-actions { display: grid; justify-items: center; gap: 7px; flex: 0 0 auto; text-align: center; }
.run-tests-button {
  position: relative; display: inline-flex; align-items: center; justify-content: center; gap: 9px;
  min-width: 190px; min-height: 46px; padding: 10px 18px;
  color: #fff; background: linear-gradient(135deg, #286fd7, #1654ad);
  border: 1px solid #225fbf; border-radius: 11px; cursor: pointer;
  box-shadow: 0 10px 22px rgba(29, 92, 183, .2);
  font: inherit; font-size: .86rem; font-weight: 750; white-space: nowrap;
}
.run-tests-button::before {
  content: ""; position: absolute; left: 16px; top: 50%; width: 8px; height: 8px;
  margin-top: -4px; border-radius: 50%;
  background: #b9dbff; box-shadow: 0 0 0 4px rgba(255, 255, 255, .12);
}
.run-tests-button:hover:not(:disabled) { background: linear-gradient(135deg, #2b77e5, #1b5fbe); }
.run-tests-button:disabled { cursor: not-allowed; opacity: .62; box-shadow: none; }
.run-tests-button[aria-busy="true"]::before {
  width: 12px; height: 12px; background: transparent; border: 2px solid rgba(255, 255, 255, .35);
  border-top-color: #fff; box-shadow: none; margin-top: -6px;
  animation: cockpit-spin .8s linear infinite;
}
.run-hint { color: var(--muted); font-size: .68rem; white-space: nowrap; }
.run-status {
  display: flex; align-items: center; gap: 9px; margin-top: 17px; padding-top: 15px;
  color: var(--muted); border-top: 1px solid var(--line); font-size: .8rem;
}
.run-status::before {
  content: ""; width: 8px; height: 8px; flex: 0 0 8px; border-radius: 50%;
  background: #98a2b3; box-shadow: 0 0 0 4px rgba(152, 162, 179, .12);
}
.run-status[data-state="running"] { color: var(--blue); }
.run-status[data-state="running"]::before { background: var(--blue); box-shadow: 0 0 0 4px rgba(29, 100, 216, .12); }
.run-status[data-state="passed"] { color: var(--green); }
.run-status[data-state="passed"]::before { background: var(--green); box-shadow: 0 0 0 4px rgba(8, 122, 85, .12); }
.run-status[data-state="failed"], .run-status[data-state="unavailable"] { color: var(--red); }
.run-status[data-state="failed"]::before,
.run-status[data-state="unavailable"]::before { background: var(--red); box-shadow: 0 0 0 4px rgba(180, 35, 24, .12); }
.api-scope {
  margin-top: 13px; overflow: hidden; background: #f8fafc;
  border: 1px solid #e2e8f0; border-radius: 11px;
}
.api-scope > summary {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  min-height: 42px; padding: 8px 12px; color: var(--ink);
  background: #f3f6fa; border: 0; border-radius: 0; font-size: .78rem;
}
.api-scope > summary::marker { content: ""; }
.api-scope > summary::-webkit-details-marker { display: none; }
.api-scope > summary::before {
  content: "+"; display: grid; place-items: center; width: 20px; height: 20px;
  flex: 0 0 20px; color: var(--blue); background: var(--blue-soft);
  border-radius: 6px; font-size: .9rem; font-weight: 800;
}
.api-scope[open] > summary::before { content: "−"; }
.api-scope-title { margin-right: auto; font-weight: 650; }
.api-scope-count { color: var(--muted); font-size: .7rem; white-space: nowrap; }
.api-groups {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px; padding: 12px;
}
.api-group { min-width: 0; padding: 12px; background: #fff; border: 1px solid #e6eaf0; border-radius: 10px; }
.api-group h3 { margin: 0 0 8px; color: var(--ink-strong); font-size: .8rem; }
.api-endpoint-list { display: grid; gap: 6px; margin: 0; padding: 0; list-style: none; }
.api-endpoint {
  display: grid; grid-template-columns: 56px minmax(0, 1fr); gap: 3px 9px;
  align-items: center; min-width: 0; padding: 6px 0; border-top: 1px solid #eef1f5;
}
.api-endpoint:first-child { padding-top: 0; border-top: 0; }
.api-method {
  display: inline-flex; align-items: center; justify-content: center; min-height: 20px;
  padding: 1px 6px; color: #315fa8; background: #eaf2ff; border-radius: 5px;
  font-family: "Cascadia Code", Consolas, monospace; font-size: .61rem; font-weight: 800;
}
.api-method.post { color: #087a55; background: #e7f7f0; }
.api-method.put { color: #8b5a00; background: #fff4dc; }
.api-method.patch { color: #7650a8; background: #f1eafd; }
.api-method.delete { color: var(--red); background: var(--red-soft); }
.api-endpoint code { min-width: 0; color: var(--ink-strong); font-size: .7rem; overflow-wrap: anywhere; }
.api-endpoint-description { grid-column: 2; color: var(--muted); font-size: .67rem; line-height: 1.45; }
.run-results { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 13px; }
.run-suite { min-width: 0; padding: 13px 14px; background: #f8fafc; border: 1px solid #e5eaf1; border-radius: 11px; }
.run-suite-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.run-suite h3 { margin: 0; color: var(--ink-strong); font-size: .82rem; }
.run-suite-meta { margin: 5px 0 0; color: var(--muted); font-size: .71rem; }
.run-suite-output { margin-top: 10px; }
.run-suite-output summary { min-height: 29px; padding: 3px 8px; }
.run-suite-output pre { max-height: 320px; }
@keyframes cockpit-spin { to { transform: rotate(360deg); } }
.content-layout {
  display: grid; grid-template-columns: minmax(0, 1.75fr) minmax(280px, .65fr);
  gap: 18px; align-items: start;
}
.stack { display: grid; gap: 18px; min-width: 0; }
.panel { min-width: 0; padding: 22px; overflow: hidden; }
.panel-head {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 20px;
  margin-bottom: 18px;
}
.section-kicker {
  margin-bottom: 4px; color: var(--blue); font-size: .69rem; font-weight: 750;
  letter-spacing: .12em; text-transform: uppercase;
}
.panel h2 { margin: 0; color: var(--ink-strong); font-size: 1.28rem; letter-spacing: -.02em; }
.panel-head p { margin: 5px 0 0; color: var(--muted); font-size: .82rem; }
.counter {
  display: inline-flex; align-items: center; justify-content: center; min-height: 30px;
  padding: 4px 10px; color: var(--muted); background: #f3f6fa;
  border: 1px solid var(--line); border-radius: 8px; font-size: .76rem; white-space: nowrap;
}
.badge {
  display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px;
  border: 1px solid transparent; border-radius: 999px; font-size: .75rem;
  font-weight: 750; line-height: 1.35; white-space: nowrap;
}
.badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.badge.passed, .badge.done { color: var(--green); background: var(--green-soft); border-color: #ccebdd; }
.badge.failed { color: var(--red); background: var(--red-soft); border-color: #f6d2cf; }
.badge.partial, .badge.in-progress, .badge.approved, .badge.blocked {
  color: var(--amber); background: var(--amber-soft); border-color: #f2dfb7;
}
.badge.skipped, .badge.unverified, .badge.draft, .badge.superseded {
  color: #596579; background: var(--neutral-soft); border-color: #dce2ea;
}
.spec-list { display: grid; gap: 10px; }
.spec-row {
  --state: #98a2b3;
  position: relative; display: grid;
  grid-template-columns: minmax(0, 1.35fr) auto minmax(150px, .62fr) minmax(150px, .62fr) auto;
  gap: 18px; align-items: center; min-width: 0; padding: 15px 16px 15px 20px;
  background: #fbfcfe; border: 1px solid #e6eaf0; border-radius: 13px;
  transition: border-color .16s ease, transform .16s ease, box-shadow .16s ease;
}
.spec-row::before {
  content: ""; position: absolute; left: -1px; top: 14px; bottom: 14px; width: 3px;
  background: var(--state); border-radius: 0 4px 4px 0;
}
.spec-row:hover {
  border-color: #ced8e6; transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(20, 32, 52, .055);
}
.spec-row.state-passed, .spec-row.state-done { --state: #1a9b71; }
.spec-row.state-partial, .spec-row.state-in-progress,
.spec-row.state-approved, .spec-row.state-blocked { --state: #d58a19; }
.spec-row.state-failed { --state: #d94851; }
.spec-main { display: flex; align-items: center; gap: 11px; min-width: 0; }
.spec-index {
  display: inline-grid; place-items: center; min-width: 30px; height: 30px;
  padding: 0 7px; flex: 0 0 auto; color: var(--muted); background: #eef3fa;
  border-radius: 8px; font-family: "Cascadia Code", Consolas, monospace;
  font-size: .7rem; font-weight: 750;
}
.spec-copy { min-width: 0; }
.spec-copy a {
  display: inline-block; max-width: 100%; color: var(--ink-strong);
  font-size: .91rem; font-weight: 720; line-height: 1.35; text-decoration: none;
  overflow-wrap: anywhere;
}
.spec-copy a:hover { color: var(--blue); text-decoration: underline; text-underline-offset: 3px; }
.spec-updated { margin-top: 3px; color: var(--muted-light); font-size: .69rem; }
.spec-progress { min-width: 0; }
.progress {
  width: 100%; height: 6px; overflow: hidden; background: #e9edf3; border-radius: 99px;
}
.progress > span {
  display: block; height: 100%; border-radius: inherit;
  background: linear-gradient(90deg, #347ee8, #42a887);
}
.progress-label {
  display: flex; justify-content: space-between; gap: 8px; margin-bottom: 6px;
  color: var(--muted); font-size: .69rem;
}
.progress-label strong { color: var(--ink); font-size: .72rem; font-weight: 700; }
.spec-date { color: var(--muted); font-size: .72rem; white-space: nowrap; text-align: right; }
.gate-list { display: grid; gap: 9px; }
.gate-row {
  --state: #98a2b3;
  min-width: 0; padding: 14px 15px; background: #fbfcfe;
  border: 1px solid #e6eaf0; border-radius: 13px;
}
.gate-row.state-passed { --state: #1a9b71; }
.gate-row.state-failed { --state: #d94851; }
.gate-row.state-partial { --state: #d58a19; }
.gate-row.state-skipped { --state: #98a2b3; }
.gate-heading {
  display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 12px;
  align-items: center; min-width: 0;
}
.gate-name { display: flex; align-items: center; gap: 10px; min-width: 0; }
.gate-dot {
  width: 9px; height: 9px; flex: 0 0 9px; border-radius: 50%;
  background: var(--state); box-shadow: 0 0 0 4px color-mix(in srgb, var(--state) 12%, transparent);
}
.gate-name strong {
  min-width: 0; color: var(--ink-strong); font-family: "Cascadia Code", Consolas, monospace;
  font-size: .8rem; font-weight: 650; overflow-wrap: anywhere;
}
.gate-time { color: var(--muted); font-variant-numeric: tabular-nums; font-size: .73rem; white-space: nowrap; }
.gate-summary {
  margin: 9px 0 0 19px; color: var(--muted); font-size: .76rem;
  line-height: 1.55; overflow-wrap: anywhere;
}
.gate-output { margin: 10px 0 0 19px; }
details { margin-top: 9px; }
summary {
  display: inline-flex; align-items: center; min-height: 32px; padding: 4px 9px;
  cursor: pointer; color: var(--red); background: #fff7f6; border: 1px solid #f2d6d3;
  border-radius: 7px; font-size: .73rem; font-weight: 650;
}
summary:hover { background: var(--red-soft); }
pre {
  max-width: 100%; margin: 10px 0 0; padding: 14px; overflow: auto;
  background: #0e1726; color: #dce6f4; border: 1px solid #26364e;
  border-radius: 10px; font-size: .73rem; line-height: 1.55; white-space: pre-wrap;
  overflow-wrap: anywhere;
}
code { font-family: "Cascadia Code", Consolas, monospace; }
.rail { display: grid; gap: 18px; min-width: 0; }
.asset-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.asset-card {
  min-width: 0; padding: 14px; background: #f7f9fc;
  border: 1px solid #e6eaf0; border-radius: 12px;
}
.asset-mark {
  display: grid; place-items: center; width: 26px; height: 26px; margin-bottom: 12px;
  color: var(--blue); background: var(--blue-soft); border-radius: 7px;
  font-size: .59rem; font-weight: 800; letter-spacing: .03em;
}
.asset-card strong {
  display: block; color: var(--ink-strong); font-size: 1.48rem;
  line-height: 1.15; font-variant-numeric: tabular-nums;
}
.asset-card span:last-child { display: block; margin-top: 3px; color: var(--muted); font-size: .71rem; }
.command-list { display: grid; gap: 8px; }
.command {
  display: flex; align-items: flex-start; gap: 9px; min-width: 0; padding: 10px 11px;
  color: #dce6f4; background: #111c2d; border: 1px solid #27364b; border-radius: 9px;
  font-size: .72rem; line-height: 1.45;
}
.command .prompt { flex: 0 0 auto; color: #66a5ff; font-weight: 800; }
.command code { min-width: 0; overflow-wrap: anywhere; }
.aside-note {
  display: flex; gap: 9px; margin: 14px 0 0; padding-top: 14px;
  color: var(--muted); border-top: 1px solid var(--line); font-size: .74rem; line-height: 1.55;
}
.aside-note::before {
  content: "i"; display: grid; place-items: center; width: 18px; height: 18px;
  flex: 0 0 18px; color: var(--blue); background: var(--blue-soft);
  border-radius: 50%; font-size: .65rem; font-weight: 800;
}
.notice {
  display: flex; align-items: flex-start; gap: 10px; margin: 0; padding: 14px 16px;
  color: var(--amber); background: var(--amber-soft); border: 1px solid #efd9ac;
  border-radius: 12px; font-size: .82rem;
}
.notice::before {
  content: "!"; display: grid; place-items: center; width: 20px; height: 20px;
  flex: 0 0 20px; color: #fff; background: var(--amber); border-radius: 50%;
  font-size: .68rem; font-weight: 800;
}
.issue-list { margin: 0; padding: 0; list-style: none; display: grid; gap: 8px; }
.issue-list li {
  padding: 10px 12px; color: var(--red); background: var(--red-soft);
  border: 1px solid #f4d2cf; border-radius: 9px; font-size: .8rem;
}
.empty-state {
  padding: 26px 18px; text-align: center; color: var(--muted);
  background: #f8fafc; border: 1px dashed var(--line-strong); border-radius: 12px;
}
.empty-state strong { display: block; margin-bottom: 3px; color: var(--ink); font-size: .92rem; }
.footer {
  display: flex; justify-content: space-between; gap: 18px; align-items: center;
  margin-top: 28px; padding-top: 18px; color: var(--muted);
  border-top: 1px solid var(--line); font-size: .73rem;
}
.footer p { margin: 0; }
.footer-links { display: flex; flex-wrap: wrap; gap: 14px; }
.footer a { color: var(--muted); text-decoration: none; }
.footer a:hover, .footer a:focus-visible { color: var(--blue); text-decoration: underline; }
.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
}
:focus-visible { outline: 2px solid #5b9cff; outline-offset: 2px; }
@media (max-width: 1100px) {
  .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .content-layout { grid-template-columns: 1fr; }
  .rail { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .spec-row {
    grid-template-columns: minmax(0, 1.3fr) auto minmax(130px, .7fr) minmax(130px, .7fr);
    gap: 14px;
  }
  .spec-date { grid-column: 1 / -1; grid-row: 2; text-align: left; }
}
@media (max-width: 760px) {
  .topbar-inner {
    width: min(100% - 24px, 1280px); flex-wrap: wrap; gap: 10px 16px; padding: 12px 0;
  }
  .topbar-context { margin-left: auto; }
  .top-nav { width: 100%; padding: 0; gap: 6px; overflow-x: auto; scrollbar-width: none; }
  .top-nav::-webkit-scrollbar { display: none; }
  .top-nav a { flex: 0 0 auto; min-height: 40px; background: rgba(255, 255, 255, .045); }
  main { width: min(100% - 24px, 1280px); padding-top: 16px; }
  .hero { grid-template-columns: 1fr; gap: 22px; padding: 24px; border-radius: 18px; }
  .hero h1 { font-size: clamp(2.05rem, 10vw, 3.3rem); }
  .status-spotlight { padding: 18px; }
  .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .metric-card { padding: 16px; }
  .regression-layout { align-items: flex-start; flex-direction: column; gap: 17px; }
  .regression-actions { justify-items: stretch; width: 100%; }
  .run-tests-button { width: 100%; }
  .run-hint { text-align: center; }
  .run-results { grid-template-columns: 1fr; }
  .api-groups { grid-template-columns: 1fr; }
  .content-layout, .rail { gap: 12px; }
  .rail { grid-template-columns: 1fr; }
  .panel { padding: 18px; border-radius: 15px; }
  .panel-head { margin-bottom: 15px; }
  .spec-row {
    grid-template-columns: 1fr auto; gap: 12px; padding: 15px;
  }
  .spec-main { grid-column: 1; }
  .spec-row > .badge { grid-column: 2; grid-row: 1; align-self: start; }
  .progress-acceptance, .progress-tasks { grid-column: 1 / -1; }
  .spec-date { grid-column: 1 / -1; grid-row: auto; text-align: left; }
  .gate-heading { grid-template-columns: minmax(0, 1fr) auto; }
  .gate-heading .badge { grid-column: 2; grid-row: 1; }
  .gate-time { grid-column: 1 / -1; grid-row: 2; margin-left: 19px; }
  .gate-summary, .gate-output { margin-left: 0; }
  .footer { align-items: flex-start; flex-direction: column; }
}
@media (max-width: 520px) {
  .brand-copy strong { font-size: .8rem; }
  .topbar-context span:last-child { display: none; }
  .hero { padding: 21px 18px; }
  .hero-copy > p { font-size: .91rem; }
  .status-spotlight { grid-template-columns: auto 1fr; gap: 13px; }
  .status-spotlight strong { font-size: 1.32rem; }
  .status-orb { width: 46px; height: 46px; flex-basis: 46px; border-radius: 13px; }
  .status-orb::before { inset: 8px; }
  .status-orb::after { font-size: 1.25rem; }
  .metrics { grid-template-columns: 1fr; }
  .metric-card { padding: 16px; }
  .metric-value { min-height: 0; }
  .spec-row { grid-template-columns: 1fr; }
  .spec-row > .badge { grid-column: 1; grid-row: auto; justify-self: start; }
  .gate-heading { grid-template-columns: 1fr; gap: 8px; }
  .gate-heading .badge { grid-column: 1; grid-row: auto; justify-self: start; }
  .gate-time { grid-column: 1; grid-row: auto; margin-left: 0; }
  .asset-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .counter { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { transition: none !important; }
}
@media print {
  .top-nav, .skip-link { display: none; }
  body { background: #fff; }
  main { width: 100%; padding: 0; }
  .hero { color: var(--ink); background: #fff; box-shadow: none; }
  .hero h1, .hero h1 span, .status-spotlight strong { color: var(--ink); }
  .metric-card, .panel { break-inside: avoid; box-shadow: none; }
}
"""

COCKPIT_JS = """
(() => {
  "use strict";

  const button = document.getElementById("run-core-tests");
  const status = document.getElementById("core-test-status");
  const results = document.getElementById("core-test-results");
  const apiScope = document.getElementById("core-test-api-scope");
  const suiteNames = {
    "backend-core": "后端核心 API",
    "frontend-unit": "前端单元测试"
  };

  if (!button || !status || !results) {
    return;
  }

  if (window.location.protocol === "file:") {
    button.disabled = true;
    button.textContent = "请先启动驾驶舱服务";
    status.dataset.state = "unavailable";
    status.textContent = "直接打开 HTML 时不能运行测试，请执行 python ai/quality/quality.py serve";
    return;
  }

  const setState = (state, message) => {
    status.dataset.state = state;
    status.textContent = message;
  };

  const buildSuite = (suite) => {
    const article = document.createElement("article");
    article.className = "run-suite";

    const head = document.createElement("div");
    head.className = "run-suite-head";

    const title = document.createElement("h3");
    title.textContent = suiteNames[suite.name] || "未知测试套件";

    const badge = document.createElement("span");
    const safeState = suite.status === "passed" ? "passed" : "failed";
    badge.className = `badge ${safeState}`;
    badge.textContent = safeState === "passed" ? "通过" : "失败";

    head.append(title, badge);
    article.append(head);

    const meta = document.createElement("p");
    meta.className = "run-suite-meta";
    const tests = Number(suite.tests) || 0;
    const duration = Number(suite.duration_seconds) || 0;
    meta.textContent = `${tests} 项测试 · ${duration.toFixed(2)} 秒`;
    article.append(meta);

    if (safeState === "failed" && suite.output) {
      const output = document.createElement("details");
      output.className = "run-suite-output";
      output.open = true;
      const summary = document.createElement("summary");
      summary.textContent = "查看失败输出";
      const pre = document.createElement("pre");
      pre.textContent = String(suite.output);
      output.append(summary, pre);
      article.append(output);
    }
    return article;
  };

  const renderResult = (data) => {
    const suites = Array.isArray(data.suites) ? data.suites : [];
    const passed = data.status === "passed";
    const totalTests = suites.reduce(
      (total, suite) => total + (Number(suite.tests) || 0),
      0
    );
    const duration = Number(data.duration_seconds) || 0;

    results.replaceChildren(...suites.map(buildSuite));
    results.hidden = false;
    setState(
      passed ? "passed" : "failed",
      passed
        ? `核心功能测试通过：${totalTests} 项 · ${duration.toFixed(2)} 秒`
        : `核心功能测试失败：${totalTests} 项完成 · ${duration.toFixed(2)} 秒`
    );
  };

  button.addEventListener("click", async () => {
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    button.textContent = "正在运行测试";
    results.hidden = true;
    if (apiScope) apiScope.open = true;
    setState("running", "正在执行后端核心 API 和前端单元测试，请稍候…");

    try {
      const response = await fetch("/api/core-tests/run", {
        method: "POST",
        headers: {
          "X-Cockpit-Test-Run": "1"
        }
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(
          (payload && payload.message) || `测试请求失败（HTTP ${response.status}）`
        );
      }
      renderResult(payload || {});
    } catch (error) {
      setState(
        "failed",
        error instanceof Error ? error.message : "无法连接本地测试服务"
      );
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      button.textContent = "再次测试核心功能";
    }
  });
})();
"""


def _load_report(path: Path) -> tuple[dict[str, Any] | None, str]:
    if not path.is_file():
        return None, "尚无验证报告；当前页面不能作为质量通过证据。"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"验证报告无法读取：{exc}"
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return None, "验证报告 schema_version 不是 1。"
    return data, ""


def _load_coverage(root: Path) -> tuple[str, str]:
    backend = "未生成"
    frontend = "未生成"
    backend_path = root / "ai" / "reports" / "backend-coverage.json"
    frontend_path = (
        root / "business/frontend/tests/unit/coverage/coverage-summary.json"
    )
    try:
        backend_data = json.loads(backend_path.read_text(encoding="utf-8"))
        backend = f"{float(backend_data['totals']['percent_covered']):.1f}%"
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        pass
    try:
        frontend_data = json.loads(frontend_path.read_text(encoding="utf-8"))
        frontend = f"{float(frontend_data['total']['lines']['pct']):.1f}%"
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        pass
    return backend, frontend


def _backend_inventory(root: Path) -> tuple[int, int]:
    backend_root = root / "business" / "UniDjango"
    apps = sum(
        1
        for path in backend_root.iterdir()
        if path.is_dir() and (path / "apps.py").is_file()
    )
    test_count = 0
    candidates = list(backend_root.rglob("tests.py")) + list(
        backend_root.rglob("test_*.py")
    )
    for path in candidates:
        try:
            test_count += len(
                re.findall(r"^\s*def\s+test_", path.read_text(encoding="utf-8"), re.M)
            )
        except (OSError, UnicodeDecodeError):
            continue
    return apps, test_count


def _frontend_inventory(root: Path) -> tuple[int, int]:
    frontend = root / "business" / "frontend"
    pages = len(list((frontend / "src/views").rglob("*.vue")))
    tests = len(list((frontend / "tests/unit").rglob("*.spec.js")))
    return pages, tests


def _percent(done: int, total: int) -> int:
    return round(done * 100 / total) if total else 0


def _progress(done: int, total: int, label: str = "完成") -> str:
    percentage = _percent(done, total)
    return (
        '<div class="progress-label">'
        f"<span>{escape(label)}</span>"
        f"<strong>{done} / {total} · {percentage}%</strong>"
        "</div>"
        f'<div class="progress" role="progressbar" aria-label="{escape(label)}进度" '
        f'aria-valuemin="0" aria-valuemax="{total}" aria-valuenow="{done}">'
        f'<span style="width: {percentage}%"></span></div>'
    )


def _safe_status(status: str) -> str:
    return re.sub(r"[^a-z-]", "", status.lower()) or "unknown"


def _status_badge(status: str, label: str | None = None) -> str:
    safe_status = _safe_status(status)
    return (
        f'<span class="badge {safe_status}">'
        f"{escape(label or status.upper())}</span>"
    )


def _detail_summary(detail: str, limit: int = 180) -> str:
    for line in detail.splitlines():
        summary = line.strip()
        if summary:
            return summary if len(summary) <= limit else summary[: limit - 1] + "…"
    return "无附加输出"


def _specs_panel(records: list[SpecRecord]) -> str:
    rows: list[str] = []
    for record in records:
        status = record.status or "unknown"
        safe_status = _safe_status(status)
        spec_path = escape(
            f"../specs/{record.name}/spec.md",
            quote=True,
        )
        identifier = record.identifier or record.name
        title = record.title or "未命名规格"
        rows.append(
            f'<article class="spec-row state-{safe_status}" role="listitem">'
            '<div class="spec-main">'
            f'<span class="spec-index">{escape(identifier)}</span>'
            '<div class="spec-copy">'
            f'<a href="{spec_path}">{escape(title)}</a>'
            f'<span class="spec-updated">{escape(identifier)} · 更新于 '
            f"{escape(record.updated or '-')}</span>"
            "</div></div>"
            f"{_status_badge(status)}"
            '<div class="spec-progress progress-acceptance">'
            f"{_progress(record.acceptance_done, len(record.acceptance), '验收')}"
            "</div>"
            '<div class="spec-progress progress-tasks">'
            f"{_progress(record.tasks_done, len(record.tasks), '任务')}"
            "</div>"
            f'<time class="spec-date">{escape(record.updated or "-")}</time>'
            "</article>"
        )
    if not rows:
        rows.append(
            '<div class="empty-state">'
            "<strong>尚未创建规格</strong>"
            "在 ai/specs/ 中建立首个规格后会显示在这里。"
            "</div>"
        )
    return (
        '<section class="panel" id="specs" aria-labelledby="specs-title">'
        '<div class="panel-head"><div>'
        '<div class="section-kicker">Delivery map</div>'
        '<h2 id="specs-title">规格进度</h2>'
        "<p>验收项与实现任务的可追踪完成情况</p>"
        "</div>"
        f'<span class="counter">{len(records)} 个规格</span>'
        "</div>"
        f'<div class="spec-list" role="list">{"".join(rows)}</div>'
        "</section>"
    )


def _report_panel(report: dict[str, Any] | None) -> str:
    panel_start = (
        '<section class="panel" id="gates" aria-labelledby="gates-title">'
        '<div class="panel-head"><div>'
        '<div class="section-kicker">Quality gates</div>'
        '<h2 id="gates-title">最近验证门禁</h2>'
        "<p>每个检查项的状态、耗时与可定位输出</p>"
        "</div>"
    )
    if report is None:
        return panel_start + (
            '<span class="counter">0 项</span></div>'
            '<div class="empty-state"><strong>尚无验证门禁结果</strong>'
            "运行 quick 或 full 后，这里会展示每项检查的状态与输出。"
            "</div></section>"
        )
    rows: list[str] = []
    gates = report.get("gates", [])
    for gate in gates:
        gate_status = str(gate.get("status", "failed"))
        safe_status = _safe_status(gate_status)
        detail = str(gate.get("detail", ""))
        detail_html = (
            '<div class="gate-output"><details>'
            "<summary>展开原始输出</summary>"
            f"<pre>{escape(detail)}</pre></details></div>"
            if gate_status == "failed" and detail
            else ""
        )
        summary = _detail_summary(detail)
        rows.append(
            f'<article class="gate-row state-{safe_status}">'
            '<div class="gate-heading">'
            '<div class="gate-name"><span class="gate-dot" aria-hidden="true"></span>'
            f'<strong>{escape(str(gate.get("name", "")))}</strong></div>'
            f'<span class="gate-time">{float(gate.get("duration_seconds", 0)):.2f}s</span>'
            f"{_status_badge(gate_status)}"
            "</div>"
            f'<p class="gate-summary">{escape(summary)}</p>'
            f"{detail_html}</article>"
        )
    if not rows:
        rows.append(
            '<div class="empty-state"><strong>报告中没有门禁记录</strong>'
            "重新运行质量验证以生成完整结果。</div>"
        )
    return panel_start + (
        f'<span class="counter">{len(gates)} 项</span></div>'
        f'<div class="gate-list">{"".join(rows)}</div>'
        "</section>"
    )


def _api_scope_panel() -> str:
    groups: list[str] = []
    for group in CORE_API_GROUPS:
        rows = "".join(
            (
                f'<li class="api-endpoint" data-api="'
                f'{escape(endpoint["method"] + " " + endpoint["path"], quote=True)}">'
                f'<span class="api-method {_safe_status(endpoint["method"])}">'
                f'{escape(endpoint["method"])}</span>'
                f'<code>{escape(endpoint["path"])}</code>'
                f'<span class="api-endpoint-description">'
                f'{escape(endpoint["description"])}</span></li>'
            )
            for endpoint in group["endpoints"]
        )
        groups.append(
            '<section class="api-group">'
            f"<h3>{escape(group['name'])}</h3>"
            f'<ul class="api-endpoint-list">{rows}</ul>'
            "</section>"
        )

    return (
        '<details id="core-test-api-scope" class="api-scope">'
        "<summary>"
        '<span class="api-scope-title">查看本次覆盖的 API</span>'
        f'<span class="api-scope-count">{api_contract_count()} 个接口组合</span>'
        "</summary>"
        f'<div class="api-groups">{"".join(groups)}</div>'
        "</details>"
    )


def build_cockpit(root: Path) -> Path:
    """Build `ai/cockpit/index.html` from specifications and quality evidence."""
    validation = load_specs(root)
    report, report_warning = _load_report(root / "ai" / "reports" / "report.json")
    backend_coverage, frontend_coverage = _load_coverage(root)
    backend_apps, backend_tests = _backend_inventory(root)
    frontend_pages, frontend_tests = _frontend_inventory(root)
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")

    status = str(report.get("status", "unverified")) if report else "unverified"
    safe_status = _safe_status(status)
    status_label = {
        "passed": "验证通过",
        "partial": "部分验证",
        "failed": "验证失败",
        "unverified": "未验证",
    }.get(status, status)
    gates = report.get("gates", []) if report else []
    passed_gates = sum(gate.get("status") == "passed" for gate in gates)
    gate_percentage = _percent(passed_gates, len(gates))
    duration = float(report.get("duration_seconds", 0)) if report else 0
    mode = str(report.get("mode", "—")).upper() if report else "未运行"
    report_caption = (
        f"{mode} 档验证 · {len(gates)} 项门禁"
        if report
        else "运行 quick 或 full 后生成质量结论"
    )
    warning_html = (
        f'<div class="notice" role="status">{escape(report_warning)}</div>'
        if report_warning
        else ""
    )
    spec_issues = "".join(
        f"<li>{escape(issue)}</li>" for issue in validation.issues
    )
    issue_html = (
        '<section class="panel" aria-labelledby="issues-title">'
        '<div class="panel-head"><div>'
        '<div class="section-kicker">Needs attention</div>'
        '<h2 id="issues-title">规格检查问题</h2>'
        "</div>"
        f'<span class="counter">{len(validation.issues)} 项</span></div>'
        f'<ul class="issue-list">{spec_issues}</ul></section>'
        if spec_issues
        else ""
    )

    output = root / "ai" / "cockpit" / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="UniDjango 规格、质量门禁与代码资产的只读工程快照">
  <meta name="color-scheme" content="light">
  <title>UniDjango 工程驾驶舱</title>
  <style>{CSS}</style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <header class="topbar">
    <div class="topbar-inner">
      <a class="brand" href="../../README.md" aria-label="返回 UniDjango 项目入口">
        <span class="brand-mark" aria-hidden="true"></span>
        <span class="brand-copy">
          <strong>UNIDJANGO</strong>
          <span>Engineering cockpit</span>
        </span>
      </a>
      <div class="topbar-context">
        <span class="context-dot" aria-hidden="true"></span>
        <span>STATIC SNAPSHOT</span>
        <time>{escape(now)}</time>
      </div>
      <nav class="top-nav" aria-label="驾驶舱导航">
        <a href="#specs">规格</a>
        <a href="#gates">门禁</a>
        <a href="#assets">资产</a>
        <a href="../docs/QUALITY_GATES.md">质量说明</a>
      </nav>
    </div>
  </header>
  <main id="main-content">
    {warning_html}
    <section class="hero" aria-labelledby="dashboard-title">
      <div class="hero-copy">
        <div class="eyebrow">Engineering health overview</div>
        <h1 id="dashboard-title">工程交付状态<br><span>一眼看清。</span></h1>
        <p>规格进度、质量门禁与代码资产，来自当前仓库的真实快照。</p>
        <div class="hero-meta" aria-label="页面特性">
          <span class="hero-chip">只读本地数据</span>
          <span class="hero-chip">无外部依赖</span>
          <span class="hero-chip">自动生成</span>
        </div>
      </div>
      <aside class="status-spotlight status-{safe_status}" aria-label="最近验证结论">
        <span class="status-orb" aria-hidden="true"></span>
        <div>
          <div class="status-caption">Quality signal</div>
          <strong>{escape(status_label)}</strong>
          <small>{escape(report_caption)}</small>
        </div>
      </aside>
    </section>

    <section class="metrics" aria-label="关键质量指标">
      <article class="metric-card metric-{safe_status}">
        <div class="metric-head">
          <span class="metric-label">最近验证</span>
          <span class="metric-mark" aria-hidden="true">QA</span>
        </div>
        <div class="metric-value">{_status_badge(status, status_label)}</div>
        <p class="metric-caption">{escape(report_caption)}</p>
      </article>
      <article class="metric-card">
        <div class="metric-head">
          <span class="metric-label">门禁通过</span>
          <span class="metric-mark" aria-hidden="true">GT</span>
        </div>
        <div class="metric-value">{passed_gates}<span class="unit">/ {len(gates)}</span></div>
        <p class="metric-caption">本轮通过率 {gate_percentage}%</p>
        <div class="metric-progress" aria-hidden="true">
          <span style="width: {gate_percentage}%"></span>
        </div>
      </article>
      <article class="metric-card">
        <div class="metric-head">
          <span class="metric-label">代码覆盖率</span>
          <span class="metric-mark" aria-hidden="true">CV</span>
        </div>
        <div class="coverage-pair">
          <div class="coverage-item"><span>后端</span><strong>{escape(backend_coverage)}</strong></div>
          <div class="coverage-item"><span>前端</span><strong>{escape(frontend_coverage)}</strong></div>
        </div>
        <p class="metric-caption">最近生成的覆盖率报告</p>
      </article>
      <article class="metric-card">
        <div class="metric-head">
          <span class="metric-label">本轮耗时</span>
          <span class="metric-mark" aria-hidden="true">TM</span>
        </div>
        <div class="metric-value">{duration:.2f}<span class="unit">秒</span></div>
        <p class="metric-caption">整轮质量门禁执行时间</p>
      </article>
    </section>

    <section class="panel regression-panel" aria-labelledby="core-tests-title">
      <div class="regression-layout">
        <div class="regression-copy">
          <div class="section-kicker">Regression check</div>
          <h2 id="core-tests-title">一键测试核心功能</h2>
          <p>运行用户、角色、菜单、部门的 Django 核心 API，以及前端基础单元测试。测试使用内存数据库和本地缓存，不会修改业务数据。</p>
          <div class="regression-chips" aria-label="测试范围">
            <span class="regression-chip">Django 核心 API</span>
            <span class="regression-chip">Jest 单元测试</span>
            <span class="regression-chip">失败输出可展开</span>
          </div>
        </div>
        <div class="regression-actions">
          <button id="run-core-tests" class="run-tests-button" type="button">一键测试核心功能</button>
          <span class="run-hint">预计 10-20 秒 · 仅本机可用</span>
        </div>
      </div>
      <div id="core-test-status" class="run-status" data-state="idle" role="status" aria-live="polite">
        尚未运行核心功能测试
      </div>
      {_api_scope_panel()}
      <div id="core-test-results" class="run-results" aria-label="核心功能测试结果" hidden></div>
      <noscript><p class="run-status" data-state="unavailable">浏览器未启用 JavaScript，请通过终端执行测试。</p></noscript>
    </section>

    <div class="content-layout">
      <div class="stack">
        {_specs_panel(validation.records)}
        {issue_html}
        {_report_panel(report)}
      </div>
      <aside class="rail" aria-label="仓库资产与常用操作">
        <section class="panel" id="assets" aria-labelledby="assets-title">
          <div class="panel-head"><div>
            <div class="section-kicker">Repository inventory</div>
            <h2 id="assets-title">代码资产</h2>
            <p>仓库中可扫描的应用与测试规模</p>
          </div></div>
          <div class="asset-grid">
            <div class="asset-card"><span class="asset-mark" aria-hidden="true">APP</span>
              <strong>{backend_apps}</strong><span>Django 应用</span></div>
            <div class="asset-card"><span class="asset-mark" aria-hidden="true">BE</span>
              <strong>{backend_tests}</strong><span>后端测试</span></div>
            <div class="asset-card"><span class="asset-mark" aria-hidden="true">PAGE</span>
              <strong>{frontend_pages}</strong><span>前端页面</span></div>
            <div class="asset-card"><span class="asset-mark" aria-hidden="true">FE</span>
              <strong>{frontend_tests}</strong><span>前端测试</span></div>
          </div>
        </section>
        <section class="panel" id="commands" aria-labelledby="commands-title">
          <div class="panel-head"><div>
            <div class="section-kicker">Runbook</div>
            <h2 id="commands-title">常用命令</h2>
            <p>从仓库根目录执行</p>
          </div></div>
          <div class="command-list">
            <div class="command"><span class="prompt" aria-hidden="true">$</span>
              <code>python ai/quality/quality.py quick</code></div>
            <div class="command"><span class="prompt" aria-hidden="true">$</span>
              <code>python ai/quality/quality.py full</code></div>
            <div class="command"><span class="prompt" aria-hidden="true">$</span>
              <code>python ai/quality/quality.py release</code></div>
            <div class="command"><span class="prompt" aria-hidden="true">$</span>
              <code>python ai/quality/quality.py serve --port 8765</code></div>
          </div>
          <p class="aside-note">一键测试只在本机服务中运行；不连接生产数据库或密钥。</p>
        </section>
      </aside>
    </div>

    <footer class="footer">
      <p>UniDjango Engineering Cockpit · 生成于 {escape(now)}</p>
      <div class="footer-links">
        <a href="../../README.md">项目入口</a>
        <a href="../docs/CODING_STANDARDS.md">编码约定</a>
        <a href="../docs/QUALITY_GATES.md">质量门禁</a>
      </div>
    </footer>
  </main>
  <script>{COCKPIT_JS}</script>
</body>
</html>
"""
    output.write_text(html, encoding="utf-8")
    return output
