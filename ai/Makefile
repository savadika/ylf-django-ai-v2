.PHONY: help quality-quick quality-full quality-release cockpit serve

PYTHON ?= python

help:
	@echo "AI 工程命令："
	@echo "  make quality-quick   快速门禁"
	@echo "  make quality-full    完整回归"
	@echo "  make quality-release 发布验证"
	@echo "  make cockpit         刷新驾驶舱"
	@echo "  make serve           启动驾驶舱"

quality-quick:
	$(PYTHON) quality/quality.py quick

quality-full:
	$(PYTHON) quality/quality.py full

quality-release:
	$(PYTHON) quality/quality.py release

cockpit:
	$(PYTHON) quality/quality.py cockpit

serve:
	$(PYTHON) quality/quality.py serve
