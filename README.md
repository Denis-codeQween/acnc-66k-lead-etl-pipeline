# 📊 ACNC 66K Lead ETL — Hybrid Data Enrichment Pipeline

> **High-performance Python ETL & Data Enrichment pipeline designed to enrich and clean 66,000+ Australian Charity (ACNC) records using Playwright Google SERP fallback, Human-in-the-Loop captcha handling, and Pandas validation.**

---

## 📌 Project Overview

Extracting contact details and verified decision-maker emails for 66,000+ registered charities from the official Australian Charities and Not-for-profits Commission (ACNC) dataset presents several engineering challenges: missing emails in public registries, strict search engine anti-bot rate limits, and massive dataset scale.

This project delivers an automated, fault-tolerant Python solution that enriches raw public registry records with verified email addresses discovered via Google SERP search, handles anti-bot rate-limiting gracefully, and exports clean, production-ready lead lists.

---

## 🏗️ Architecture & Pipeline Strategy

```text
┌─────────────────────────────────┐
│ Raw ACNC Registry Data          │ (66,000+ Records, data.gov.au)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ Google SERP Enrichment Engine   │ (Playwright + Smart Pauses)
│  - Custom Manual Overrides      │
│  - Google SERP Extraction       │
│  - Human-in-the-Loop Captcha    │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ State Persistence & Checkpoints │ (Auto-saves every 50 records)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ Data Transformation & Cleanup   │ (Pandas ETL Workflow)
│  - Remove "Not found" / NaNs    │
│  - Filter Out Invalid Domains   │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ Final Verified Lead Output      │ (Clean Excel File: 3,886+ Rows)
└─────────────────────────────────┘
