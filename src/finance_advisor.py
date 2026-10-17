"""Isolated remuneration advisor UI. Replace tax assumptions with official tables before production advice."""
import html

def render_advisor() -> str:
    return """
<section class="results" id="consultor" style="margin:22px 0">
<h2>Consultor de Remuneração · CLT × PJ × B2B</h2>
<p class="section-sub">Compare cenários anuais. Valores ilustrativos, não equivalentes ao líquido tributário.</p>
<div class="controls" style="grid-template-columns:repeat(auto-fit,minmax(170px,1fr))">
<div><label for="fc-clt">CLT bruto (R$/mês)</label><input id="fc-clt" type="number" min="0" value="15000"></div>
<div><label for="fc-benefits">Benefícios CLT (R$/mês)</label><input id="fc-benefits" type="number" min="0" value="1500"></div>
<div><label for="fc-pj">PJ (R$/mês)</label><input id="fc-pj" type="number" min="0" value="20000"></div>
<div><label for="fc-b2b">B2B (US$/mês)</label><input id="fc-b2b" type="number" min="0" value="5000"></div>
<div><label for="fc-fx">USD/BRL (premissa)</label><input id="fc-fx" type="number" min="0" step=".01" value="5.20"></div>
<div><label for="fc-tax">Alíquota PJ estimada (%)</label><input id="fc-tax" type="number" min="0" max="100" value="12"></div>
<div><label for="fc-cost">Custos PJ (R$/mês)</label><input id="fc-cost" type="number" min="0" value="700"></div>
<div><label for="fc-months">Meses faturados/ano</label><input id="fc-months" type="number" min="0" max="12" value="11"></div>
</div>
<div id="fc-results" role="status" aria-live="polite" style="margin-top:18px"></div>
<p class="section-sub" style="margin-top:12px">CLT: total bruto anual incluindo 13º, adicional de férias e benefícios, sem IRRF/INSS ou FGTS. PJ/B2B: projeção após alíquota informada e custos; não calcula DAS, fator R, pró-labore, INSS, IRPF, retenções, spread cambial nem regras de exportação. Consulte um contador antes de decidir.</p>
</section>
<script>
(function(){
const ids=['clt','benefits','pj','b2b','fx','tax','cost','months'];
const val=k=>Math.max(0,Number(document.getElementById('fc-'+k).value)||0);
const money=n=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(n);
function update(){
const rate=Math.min(100,val('tax'))/100, months=Math.min(12,val('months')),cost=val('cost');
const clt=val('clt')*(13+1/3)+val('benefits')*12;
const pj=(val('pj')*(1-rate)-cost)*months;
const b2b=(val('b2b')*val('fx')*(1-rate)-cost)*months;
document.getElementById('fc-results').textContent='CLT bruto anual: '+money(clt)+' | PJ anual estimado: '+money(pj)+' | B2B anual estimado: '+money(b2b)+'. Não há recomendação automática sem apuração tributária e análise de benefícios.';
}
ids.forEach(k=>document.getElementById('fc-'+k).addEventListener('input',update));update();
})();
</script>
"""
