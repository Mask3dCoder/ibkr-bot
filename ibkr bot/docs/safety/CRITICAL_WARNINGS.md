# ⚠️  CRITICAL SAFETY WARNINGS ⚠️

## THIS SYSTEM TRADES REAL MONEY

Before deploying this platform to production, you **MUST** understand and accept the following risks and requirements.

---

## 🚨 TOP 10 WAYS TO LOSE ALL YOUR MONEY 🚨

### 1. **Running Untested Code in Production**
- **RISK**: Fat finger errors, infinite loops, logic bugs can drain account in seconds
- **PROTECTION**: Minimum 30 days paper trading with perfect operation
- **VALIDATION**: Review every single order manually during paper trading

### 2. **Disabling Risk Checks "Temporarily"**
- **RISK**: One unvalidated order can violate margin, hit position limits, cause liquidation
- **PROTECTION**: NEVER bypass pre-trade checks, even to "test quickly"
- **VALIDATION**: All risk checks must pass 100% of the time

### 3. **No Position Limits**
- **RISK**: Single position grows to entire account size, concentration risk explodes
- **PROTECTION**: Set max position size to 5-10% of account initially
- **VALIDATION**: Monitor position sizes multiple times per day

### 4. **No Circuit Breakers**
- **RISK**: Strategy loses money continuously until account is empty
- **PROTECTION**: Maximum daily loss must trigger automatic halt
- **VALIDATION**: Test circuit breaker activation monthly

### 5. **Trusting Market Data Blindly**
- **RISK**: Stale data, crossed markets, bad ticks cause terrible orders
- **PROTECTION**: Implement sanity checks (collar, staleness, crossed markets)
- **VALIDATION**: Log and alert on all data quality issues

### 6. **No Position Reconciliation**
- **RISK**: System thinks you have different positions than broker
- **PROTECTION**: Reconcile positions every 5 minutes automatically
- **VALIDATION**: Manual reconciliation at start/end of day

### 7. **Running Multiple Instances**
- **RISK**: Duplicate orders, double-sized positions, impossible to track
- **PROTECTION**: Use locking mechanism, never run >1 instance
- **VALIDATION**: Check for running processes before starting

### 8. **No Monitoring/Alerting**
- **RISK**: System fails, positions move against you, nobody knows
- **PROTECTION**: 24/7 monitoring, PagerDuty alerts, SMS notifications
- **VALIDATION**: Test alerting weekly

### 9. **Starting with Large Positions**
- **RISK**: Even "safe" strategies can lose; losses amplified by size
- **PROTECTION**: Start with 1% of target size, scale up over months
- **VALIDATION**: Never increase size >50% per month

### 10. **No Kill Switch**
- **RISK**: System goes haywire, can't stop it
- **PROTECTION**: Physical button or hotkey to halt ALL trading instantly
- **VALIDATION**: Test kill switch weekly

---

## 📋 MANDATORY PRE-PRODUCTION CHECKLIST

### Code Quality
- [ ] All unit tests passing (100% critical path coverage)
- [ ] All integration tests passing
- [ ] `mypy --strict` returns zero errors
- [ ] `ruff check` returns zero errors
- [ ] Performance tests show <1ms latency on hot path
- [ ] Load tests show system stable under 10x expected volume
- [ ] Code review by at least 2 senior developers
- [ ] Security audit completed (no hardcoded secrets)

### Configuration
- [ ] All secrets in environment variables or vault (NEVER in code)
- [ ] Database passwords are strong (20+ characters)
- [ ] IBKR account is correct (paper vs live)
- [ ] IBKR port matches account type (7497=paper, 7496=live)
- [ ] Risk limits are conservative (start very small)
- [ ] Circuit breakers are enabled and tested
- [ ] Kill switch is configured and accessible

### Infrastructure
- [ ] PostgreSQL + TimescaleDB running and accessible
- [ ] Redis running and accessible
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards configured
- [ ] Log aggregation working (ELK/Loki)
- [ ] Backups configured (daily minimum)
- [ ] Disaster recovery plan documented and tested

### Paper Trading (MINIMUM 30 DAYS)
- [ ] Run 30+ consecutive days without errors
- [ ] Zero position reconciliation discrepancies
- [ ] All executed orders match expectations
- [ ] P&L attribution is accurate
- [ ] Strategies perform as expected
- [ ] Risk limits enforce correctly
- [ ] Circuit breakers trigger correctly
- [ ] System recovers from crashes gracefully
- [ ] Network disconnects handled properly
- [ ] All alerts fire correctly

### Production Preparation
- [ ] Runbook for normal operations complete
- [ ] Runbook for disasters complete
- [ ] On-call rotation established
- [ ] Team trained on emergency procedures
- [ ] Manual override procedures documented
- [ ] Broker contact information readily available
- [ ] Legal/compliance review if required

### Initial Production (Start TINY)
- [ ] Start with 1-5% of target position sizes
- [ ] Run ONLY ONE strategy initially
- [ ] Monitor 24/7 for first week
- [ ] Review every single order manually for first week
- [ ] Check positions multiple times per day
- [ ] Be ready to kill switch at any time

---

## 🛑 CRITICAL OPERATIONAL RULES

### NEVER:
1. ❌ Run production code without 30+ days successful paper trading
2. ❌ Disable pre-trade risk checks for any reason
3. ❌ Trade without position limits configured
4. ❌ Use market orders without price protection
5. ❌ Ignore order rejections or errors
6. ❌ Assume positions match without reconciliation
7. ❌ Run without monitoring and alerting active
8. ❌ Skip daily position/P&L review
9. ❌ Modify risk limits without team approval
10. ❌ Run multiple instances of the platform
11. ❌ Deploy changes on Friday (need time to monitor)
12. ❌ Deploy changes before major market events
13. ❌ Trade without understanding failure modes
14. ❌ Keep silent about errors or concerns
15. ❌ Trade when unwell or stressed

### ALWAYS:
1. ✅ Start with minimum position sizes
2. ✅ Paper trade every change for 1+ week
3. ✅ Monitor systems continuously (especially new deployments)
4. ✅ Have kill switch immediately accessible
5. ✅ Maintain complete audit trail of all orders
6. ✅ Reconcile positions multiple times daily
7. ✅ Review logs daily for warnings/errors
8. ✅ Test disaster recovery monthly
9. ✅ Keep runbooks up to date
10. ✅ Know how to manually close positions
11. ✅ Have backup connectivity to market
12. ✅ Communicate issues immediately to team
13. ✅ Stop trading if anything seems wrong
14. ✅ Take mental health seriously (trading is stressful)
15. ✅ Document every incident for learning

---

## 🚑 EMERGENCY PROCEDURES

### If System Goes Haywire
1. **IMMEDIATELY**: Activate kill switch (stops all new orders)
2. **VERIFY**: Check positions with broker directly
3. **CANCEL**: All open orders manually through broker platform
4. **CLOSE**: All positions if necessary (manual execution)
5. **INVESTIGATE**: Review logs to understand what happened
6. **DOCUMENT**: Write incident report
7. **FIX**: Address root cause before restarting

### If You See Unusual Behavior
1. **STOP**: Activate kill switch immediately
2. **CHECK**: Verify positions with broker
3. **REVIEW**: Recent logs and metrics
4. **ESCALATE**: Call team if needed
5. **DOCUMENT**: What you observed
6. **INVESTIGATE**: Before restarting

### If Network Disconnects
1. **DON'T PANIC**: System should handle gracefully
2. **WAIT**: For automatic reconnection (up to 10 minutes)
3. **VERIFY**: Positions match after reconnect
4. **CHECK**: No duplicate orders were submitted
5. **RECONCILE**: Positions if any discrepancy
6. **LOG**: Incident for future reference

### If Exchange Has Issues
1. **MONITOR**: Exchange status pages
2. **REDUCE**: Trading activity or halt completely
3. **WIDEN**: Risk limits temporarily if needed
4. **COMMUNICATE**: With team about market conditions
5. **DOCUMENT**: How strategies performed

---

## 📊 DAILY OPERATIONAL CHECKLIST

### Every Morning (Before Market Open)
- [ ] Check system health (all services running)
- [ ] Verify IBKR connection
- [ ] Review overnight logs for errors
- [ ] Reconcile positions with broker
- [ ] Verify cash balance matches
- [ ] Check risk limits are configured correctly
- [ ] Review market calendar for events
- [ ] Confirm team members are available

### During Market Hours
- [ ] Monitor dashboard continuously
- [ ] Check for unusual P&L movements
- [ ] Verify strategies are behaving normally
- [ ] Watch for error messages or alerts
- [ ] Be ready to activate kill switch
- [ ] Reconcile positions every 2-4 hours

### End of Day
- [ ] Reconcile final positions with broker
- [ ] Review daily P&L and attribution
- [ ] Check all orders were as expected
- [ ] Review logs for any warnings
- [ ] Verify no orphaned orders
- [ ] Document any issues or anomalies
- [ ] Plan for next trading day

### Weekly
- [ ] Review strategy performance
- [ ] Analyze fill quality and slippage
- [ ] Check risk metrics trends
- [ ] Review and update risk limits if needed
- [ ] Test kill switch functionality
- [ ] Review and update runbooks
- [ ] Team meeting to discuss issues

### Monthly
- [ ] Full disaster recovery drill
- [ ] Review and update procedures
- [ ] Audit trail verification
- [ ] Performance review of all strategies
- [ ] Risk limit review and adjustment
- [ ] Infrastructure health check
- [ ] Training on any system updates

---

## ⚖️  LEGAL DISCLAIMER

**This software is provided for educational and research purposes only.**

Trading involves substantial risk of loss. Past performance is not indicative of future results. This software is provided "AS IS" without warranty of any kind, either express or implied.

The developers, contributors, and any affiliated parties are NOT responsible for:
- Any trading losses incurred
- System failures or bugs
- Data inaccuracies
- Market losses
- Regulatory violations
- Emotional distress
- Financial ruin

**By using this software, you acknowledge:**
1. Trading is extremely risky
2. You can lose more than your initial investment
3. You are solely responsible for your trading decisions
4. You understand all risks involved
5. You have tested extensively in paper trading
6. You will operate within legal and regulatory requirements
7. You will seek professional advice if needed

**NEVER RISK MORE THAN YOU CAN AFFORD TO LOSE.**

---

## 🎓 EDUCATION REQUIREMENTS

Before running this platform, you should understand:

### Technical
- Python asyncio and event-driven programming
- Database design and time-series data
- Distributed systems and failure modes
- Monitoring and observability
- Network programming and protocols

### Trading
- Market microstructure
- Order types and their uses
- Market impact and slippage
- Position sizing and risk management
- Portfolio theory and diversification
- Options pricing (if trading options)

### Mathematics
- Statistics and probability
- Time series analysis
- Risk metrics (VaR, Sharpe, etc.)
- Optimization techniques

### Regulatory
- Securities regulations in your jurisdiction
- Margin requirements
- Pattern day trading rules (if applicable)
- Tax implications of trading
- Reporting requirements

---

## 📞 GETTING HELP

If you encounter issues:

1. **Check logs first** - Most issues are logged
2. **Review metrics** - Prometheus/Grafana dashboards
3. **Check broker platform** - Verify positions/orders independently
4. **Review documentation** - Implementation plan and walkthroughs
5. **Test in paper mode** - Reproduce issue safely
6. **Document thoroughly** - What happened, when, why

For severe issues:
- Have backup communication channels
- Know your broker's emergency contact
- Have manual trading capability ready
- Don't hesitate to halt all trading

---

## ✅ REMEMBER

- **Start small, scale gradually**
- **Test everything exhaustively**
- **Monitor continuously**
- **Document thoroughly**
- **Never get complacent**
- **Take breaks when stressed**
- **Learn from every mistake**
- **Protect your capital first**

**The goal is to stay in the game long-term, not make quick money.**

---

*Last Updated: 2026-01-04*
*Review this document monthly and after any incident*
