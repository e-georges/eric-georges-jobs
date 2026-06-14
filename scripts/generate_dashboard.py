import json
import os
from datetime import datetime

def score_color(score):
    if score >= 80: return "#1D5C2E"
    if score >= 60: return "#C5A028"
    if score >= 40: return "#1A3C5E"
    return "#8B1A1A"

def score_label(score):
    if score >= 80: return "🔥 Top Match"
    if score >= 60: return "⚡ Bon Match"
    if score >= 40: return "👀 À évaluer"
    return "❄️ Faible"

def contract_badge(contract):
    c = contract.lower()
    if any(x in c for x in ["mission", "freelance", "interim", "indépendant"]):
        return "Freelance", "#2C2C6E"
    if "cdi" in c: return "CDI", "#1D5C2E"
    if "cdd" in c: return "CDD", "#C5A028"
    return contract, "#1A3C5E"

def generate_card(job, idx):
    score = job.get("score", 0)
    color = score_color(score)
    label = score_label(score)
    contract_text, contract_color = contract_badge(job.get("contract", ""))
    cv = job.get("cv_recommended", "CDI")
    cv_color = "#2C2C6E" if cv == "Freelance" else "#1A3C5E"
    
    return f"""
    <div class="card" style="border-left-color:{color}">
      <div class="score-badge" style="background:{color}">
        {label} — {score}/100
      </div>
      
      <div class="card-header">
        <div class="card-icon">💼</div>
        <div>
          <div class="card-title">{job.get('title','')}</div>
          <div class="card-company">🏢 {job.get('company','Non précisé')} &nbsp;·&nbsp; 📍 {job.get('location','')}</div>
        </div>
      </div>

      <div class="card-meta">
        <span class="tag" style="background:{contract_color};color:white">{contract_text}</span>
        <span class="tag">💰 {job.get('salary','Non précisé')}</span>
        <span class="tag">📅 {job.get('date','')[:10]}</span>
        <span class="tag">🔗 {job.get('source','')}</span>
      </div>

      <div class="card-body">{job.get('ai_summary','')}</div>

      <div class="card-cv" style="border-left:3px solid {cv_color}">
        📄 CV recommandé : <span style="color:{cv_color};font-weight:700">{cv}</span>
        &nbsp;·&nbsp; <span style="font-weight:400;color:#555">{job.get('title_rewrite','')}</span>
      </div>

      <div class="card-actions">
        <a class="btn btn-primary" href="{job.get('url','#')}" target="_blank">🔗 Voir l'offre</a>
        <select class="status-select" onchange="updateStatus('{job.get('id',idx)}', this.value)">
          <option value="new">● Nouvelle</option>
          <option value="active">✅ À postuler</option>
          <option value="applied">✉ Envoyée</option>
          <option value="network">◎ Réseau</option>
          <option value="rejected">✗ Refusée</option>
        </select>
        <button
