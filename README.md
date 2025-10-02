# 🚀 PayFlow — AI-Powered Payroll Variable Analysis

[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An advanced Django application for automated payroll variable extraction and analysis using AI agents and real-time interactive visualizations.

> 🏆 **This project was built during the [Agents Hackathon — Hugging Face × Anthropic × Unaite](https://luma.com/qpimrbx3) (Paris, June 15) and WON the hackathon’s top prize!**

---

## 🎯 Overview

**PayFlow** transforms how French collective bargaining agreements (CBAs) are analyzed by automating the detection and generation of payroll variables.  
Using sophisticated AI agents and a modern web interface, it turns complex legal texts into actionable payroll intelligence.

### ✨ Key Features

| 🤖 **AI Agents** | 📊 **Interactive Visuals** | 🔍 **Monitoring** |
|------------------|---------------------------|-------------------|
| Context-aware analysis | Interactive Highcharts graphs | Real-time dashboard |
| Automatic payroll variable detection | NetworkGraph relations | AI agent activity tracking |
| NetworkX integration | Timeline of variable creation | Performance metrics |
| Claude AI for legal text analysis | Pie & sector charts | Agent state/statistics |

---

## 🚀 Quick Start

### Automatic (recommended)
```bash
git clone https://github.com/AyoubSaidane/payflow.git
cd payflow
./start_app.sh

### Manual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

pip install -r requirements.txt
cp .env.example .env  # configure your Anthropic API key
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## ⚙️ Configuration

Create a `.env` file with:

```env
ANTHROPIC_API_KEY=your-anthropic-api-key
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

> ⚠️ **Security:** Never commit real API keys.

---

## 🌐 Web Interface

| URL             | Description                   |
| --------------- | ----------------------------- |
| `/`             | Main dashboard                |
| `/conventions/` | Manage and analyze CBAs       |
| `/monitoring/`  | Real-time AI agent monitoring |
| `/admin/`       | Django admin                  |

---

## 🔄 Workflow

1. **📥 Import CBA** — Retrieve legal articles from Légifrance API
2. **🤖 AI Analysis** — PayFlow agents detect and structure payroll variables
3. **📊 Visualization** — Interactive Highcharts graphs, JSON export
4. **🔍 Monitoring** — Real-time agent activity and metrics

---

## 🏗️ Tech Architecture

```
🌐 Django Web App
 ├─ Views & Templates
 ├─ AI Services (Claude)
 ├─ Real-time Monitoring (SSE)
 └─ External APIs: Légifrance + Anthropic
```

---

## 🔧 Technologies

| Area          | Tools                                  |
| ------------- | -------------------------------------- |
| Backend       | Django 4.2+, Python 3.8+               |
| AI / ML       | Anthropic Claude, smolagents, NetworkX |
| Frontend      | Bootstrap 5, Tabler, Highcharts        |
| Database      | SQLite (dev), PostgreSQL (prod)        |
| Real-time     | Server-Sent Events                     |
| External APIs | French Légifrance (legal data)         |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ to simplify French payroll CBA analysis**

⭐ [Star the repo](https://github.com/AyoubSaidane/payflow) if you like it!

</div>
```

✅ This uses **standard GitHub Markdown** — tables, code blocks, and headings render perfectly without extra spacing or strange formatting.
