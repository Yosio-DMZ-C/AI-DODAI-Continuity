'use strict';

// AgentOS-C Decision Calculator v0.1
// No network requests, third-party dependencies, or interpretation of laws/market prices.
(function () {
  function money(value, name) {
    if (!Number.isSafeInteger(value) || value < 0 || value > 1000000000) {
      throw new RangeError(name + ' must be an integer from 0 to 1,000,000,000 (万円)');
    }
    return value;
  }

  function monthlyPaymentYen(principalManYen, annualRatePercent, years) {
    money(principalManYen, 'principal_man_yen');
    if (typeof annualRatePercent !== 'number' || !Number.isFinite(annualRatePercent) ||
        annualRatePercent < 0 || annualRatePercent > 30) {
      throw new RangeError('annual_interest_rate_percent must be between 0 and 30');
    }
    if (!Number.isInteger(years) || years < 1 || years > 50) {
      throw new RangeError('loan_term_years must be an integer from 1 to 50');
    }
    var principalYen = principalManYen * 10000;
    var months = years * 12;
    if (annualRatePercent === 0) return Math.round(principalYen / months);
    var monthlyRate = annualRatePercent / 1200;
    return Math.round(principalYen * monthlyRate /
      (1 - Math.pow(1 + monthlyRate, -months)));
  }

  function calculate(raw) {
    if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
      throw new TypeError('Input must be a JSON object');
    }
    var required = [
      'purchase_price_man_yen', 'savings_man_yen', 'down_payment_man_yen',
      'closing_costs_man_yen', 'minimum_reserve_man_yen'
    ];
    var values = {};
    required.forEach(function (key) { values[key] = money(raw[key], key); });
    var price = values.purchase_price_man_yen;
    var savings = values.savings_man_yen;
    var down = values.down_payment_man_yen;
    var costs = values.closing_costs_man_yen;
    var reserve = values.minimum_reserve_man_yen;
    if (down > price) throw new RangeError('Down payment exceeds purchase price');
    var rate = raw.annual_interest_rate_percent;
    var years = raw.loan_term_years;
    // Also validates rate and term on zero-principal inputs.
    var plannedMonthly = monthlyPaymentYen(price - down, rate, years);
    var remaining = savings - down - costs;
    var affordableDown = savings - costs - reserve;
    var alternativeDown = affordableDown >= 0 ? Math.min(price, affordableDown) : null;
    var alternativeLoan = alternativeDown === null ? null : price - alternativeDown;

    return {
      schema_version: '0.1.0',
      inputs: Object.assign({}, values, {
        annual_interest_rate_percent: rate, loan_term_years: years
      }),
      cash: {
        after_planned_purchase_man_yen: remaining,
        shortfall_to_pay_initial_costs_man_yen: Math.max(0, -remaining),
        shortfall_to_keep_reserve_man_yen: Math.max(0, reserve - remaining),
        maximum_down_payment_keeping_reserve_man_yen: alternativeDown
      },
      mortgage: {
        planned_loan_man_yen: price - down,
        planned_monthly_payment_yen: plannedMonthly,
        reserve_preserving_loan_man_yen: alternativeLoan,
        reserve_preserving_monthly_payment_yen:
          alternativeLoan === null ? null : monthlyPaymentYen(alternativeLoan, rate, years)
      },
      checks: {
        cash_to_pay_initial_costs: remaining >= 0,
        reserve_preserved: remaining >= reserve,
        reserve_possible_without_extra_money: affordableDown >= 0
      },
      limitations: [
        '金額は万円の整数入力。結果の返済額は円単位に四捨五入した元利均等の概算。',
        '金利は入力した仮定値を一定とする。市場金利、税金、ローン審査、法制度は検証しない。',
        '管理費、修繕積立金、引越費用、教育費などは自動算入しない。',
        '現金不足の検査であり、購入や返済の安全性を判定するものではない。'
      ]
    };
  }

  var api = { calculate: calculate, monthlyPaymentYen: monthlyPaymentYen };
  if (typeof window !== 'undefined') window.DecisionCalculator = api;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
    if (require.main === module) {
      try {
        var fs = require('node:fs');
        var path = process.argv[2];
        var text = path && path !== '-' ? fs.readFileSync(path, 'utf8') : fs.readFileSync(0, 'utf8');
        process.stdout.write(JSON.stringify(calculate(JSON.parse(text)), null, 2) + '\n');
      } catch (error) {
        process.stderr.write('ERROR: ' + error.message + '\n');
        process.exitCode = 1;
      }
    }
  }
})();
