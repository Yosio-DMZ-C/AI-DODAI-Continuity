'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const calc = require('./calculator.js');

const baseline = {
  purchase_price_man_yen: 3800,
  savings_man_yen: 900,
  down_payment_man_yen: 700,
  closing_costs_man_yen: 300,
  minimum_reserve_man_yen: 300,
  annual_interest_rate_percent: 1,
  loan_term_years: 35
};

test('T1 detects immediate cash shortage and required reserve gap', () => {
  const out = calc.calculate(baseline);
  assert.equal(out.cash.after_planned_purchase_man_yen, -100);
  assert.equal(out.cash.shortfall_to_pay_initial_costs_man_yen, 100);
  assert.equal(out.cash.shortfall_to_keep_reserve_man_yen, 400);
  assert.equal(out.checks.cash_to_pay_initial_costs, false);
  assert.equal(out.checks.reserve_preserved, false);
});

test('T1 calculates a reserve-preserving alternative without making recommendations', () => {
  const out = calc.calculate(baseline);
  assert.equal(out.cash.maximum_down_payment_keeping_reserve_man_yen, 300);
  assert.equal(out.mortgage.planned_loan_man_yen, 3100);
  assert.equal(out.mortgage.reserve_preserving_loan_man_yen, 3500);
  assert.equal(out.mortgage.planned_monthly_payment_yen, 87509);
  assert.equal(out.checks.reserve_possible_without_extra_money, true);
});

test('exactly meeting reserve is accepted', () => {
  const out = calc.calculate({ ...baseline, down_payment_man_yen: 300 });
  assert.equal(out.cash.after_planned_purchase_man_yen, 300);
  assert.equal(out.cash.shortfall_to_keep_reserve_man_yen, 0);
  assert.equal(out.checks.reserve_preserved, true);
});

test('no reserve-preserving down payment when closing costs exceed available cash', () => {
  const out = calc.calculate({ ...baseline, savings_man_yen: 500, closing_costs_man_yen: 300, minimum_reserve_man_yen: 300 });
  assert.equal(out.checks.reserve_possible_without_extra_money, false);
  assert.equal(out.cash.maximum_down_payment_keeping_reserve_man_yen, null);
  assert.equal(out.mortgage.reserve_preserving_loan_man_yen, null);
  assert.equal(out.mortgage.reserve_preserving_monthly_payment_yen, null);
});

test('a fully paid property produces zero mortgage', () => {
  const out = calc.calculate({ ...baseline, purchase_price_man_yen: 100, down_payment_man_yen: 100, savings_man_yen: 500 });
  assert.equal(out.mortgage.planned_loan_man_yen, 0);
  assert.equal(out.mortgage.planned_monthly_payment_yen, 0);
});

test('zero interest is linear principal divided by months', () => {
  assert.equal(calc.monthlyPaymentYen(360, 0, 30), 10000);
});

test('1% to 2% rate sensitivity is computed rather than guessed', () => {
  const diff = calc.monthlyPaymentYen(3100, 2, 35) - calc.monthlyPaymentYen(3100, 1, 35);
  assert.equal(diff, 15182);
});

test('input validation rejects non-integer monetary values', () => {
  assert.throws(() => calc.calculate({ ...baseline, down_payment_man_yen: 700.1 }), RangeError);
});

test('input validation rejects negative monetary values', () => {
  assert.throws(() => calc.calculate({ ...baseline, savings_man_yen: -1 }), RangeError);
});

test('input validation rejects down payment above price', () => {
  assert.throws(() => calc.calculate({ ...baseline, down_payment_man_yen: 4000 }), RangeError);
});

test('input validation rejects missing input and invalid object', () => {
  assert.throws(() => calc.calculate({ ...baseline, closing_costs_man_yen: undefined }), RangeError);
  assert.throws(() => calc.calculate(null), TypeError);
});

test('input validation rejects nonfinite/negative/out-of-range interest', () => {
  for (const rate of [NaN, Infinity, -1, 31, '1']) {
    assert.throws(() => calc.calculate({ ...baseline, annual_interest_rate_percent: rate }), RangeError);
  }
});

test('input validation rejects fractional/zero/out-of-range years', () => {
  for (const years of [0, 35.5, 51, '35']) {
    assert.throws(() => calc.calculate({ ...baseline, loan_term_years: years }), RangeError);
  }
});

test('CLI accepts fixture JSON and emits the same result as library API', () => {
  const fixture = path.join(__dirname, 'example.json');
  const output = cp.execFileSync(process.execPath, [path.join(__dirname, 'calculator.js'), fixture], { encoding: 'utf8' });
  assert.deepEqual(JSON.parse(output), calc.calculate(JSON.parse(fs.readFileSync(fixture, 'utf8'))));
});

test('CLI reports invalid input and exits nonzero', () => {
  const run = cp.spawnSync(process.execPath, [path.join(__dirname, 'calculator.js'), '-'], { input: '{"savings_man_yen":3}', encoding: 'utf8' });
  assert.equal(run.status, 1);
  assert.match(run.stderr, /ERROR:/);
});

test('browser interface reuses the same library with no remote scripts', () => {
  const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
  assert.match(html, /src="\.\/calculator\.js"/);
  assert.match(html, /DecisionCalculator\.calculate\(input\)/);
  assert.doesNotMatch(html, /<script[^>]+src=["']https?:/);
  assert.doesNotMatch(html, /\bfetch\s*\(/);
});
