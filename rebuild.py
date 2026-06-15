# -*- coding: utf-8 -*-
"""
rebuild.py — 一键重新生成 index.html
用法: python rebuild.py

流程:
  1. 读取 题库.txt → 解析为结构化数据 → 保存 题库.json
  2. 读取 题库.json → 内嵌到 HTML 模板中 → 保存 index.html

前提: 题库.txt 格式需保持为「板块名 + 题型 + 编号题目」的结构。
      板块名: 独立一行（如"地面火炬"）
      题型: 独立一行（选择题 / 填空题 / 判断题 / 简答题）
      题目: 数字编号开头，占一行或多行

注意事项:
  - 选择题格式: 题目（X. 答案）。  —— 括号内的 X. 答案会被解析
  - 填空题格式: 题目（答案1）……（答案2）  —— 多个括号对应多个空
  - 判断题格式: 题目（√）或题目（×） —— 括号内 √ 或 ×
  - 简答题格式: 题目。答案全文  —— 句号后为答案
  - 简答题答案中不要包含原始换行符（会被合并为空格）
"""

import re
import json

# ============================================================
# 配置: 板块列表和题型列表（与 题库.txt 中保持一致）
# ============================================================
SECTIONS = [
    "地面火炬", "给水加压泵站", "罐区", "锅炉", "空压站",
    "污水预处理", "循环水站", "制氮站", "制冷站"
]
SUBTYPES = ["选择题", "填空题", "判断题", "简答题"]

TXT_PATH = "题库.txt"
JSON_PATH = "题库.json"
HTML_PATH = "index.html"

# ============================================================
# 第 1 步: 解析 题库.txt → 题库.json
# ============================================================
print("[1/3] 解析 题库.txt ...")

with open(TXT_PATH, encoding="utf-8") as f:
    lines = [l.rstrip('\r\n') for l in f]  # 归一化换行符

# 定位各板块的起始行
sec_map = {}
for i, line in enumerate(lines):
    t = line.strip()
    if t in SECTIONS:
        sec_map[t] = i

result = {}
sec_names = [s for s in SECTIONS if s in sec_map]

for idx, sec in enumerate(sec_names):
    start = sec_map[sec]
    end = sec_map[sec_names[idx+1]] if idx+1 < len(sec_names) else len(lines)
    block = lines[start:end]

    # 定位各题型的起始行
    sub_idx = {}
    for i, line in enumerate(block):
        t = line.strip()
        if t in SUBTYPES:
            sub_idx[t] = i

    section_data = {}
    sub_names = [s for s in SUBTYPES if s in sub_idx]

    for si, sub in enumerate(sub_names):
        s_start = sub_idx[sub]
        s_end = sub_idx[sub_names[si+1]] if si+1 < len(sub_names) else len(block)
        q_lines = block[s_start+1:s_end]
        text = "\n".join(q_lines)

        questions = []

        if sub == "选择题":
            # 格式: 题目（X. 答案）。→ 题目替换为（    ），答案提取 X. 答案
            parts = re.split(r'(?:^|\n)(\d+)\.\s*', text)
            for pi in range(1, len(parts)-1, 2):
                q_text = parts[pi+1].strip()
                m = re.search(r'[（(]([A-D])\.\s*([^）)]+?)[）)]', q_text)
                if m:
                    answer_full = m.group(1) + ". " + m.group(2).strip()
                    # 把答案位置替换为空括号占位
                    q_clean = re.sub(
                        r'[（(][A-D]\.\s*[^）)]+?[）)][。；;.]?\s*',
                        '\uff08    \uff09', q_text
                    ).strip().rstrip('。；;.')
                    questions.append({"q": q_clean, "answer": answer_full})
                else:
                    questions.append({"q": q_text, "answer": "?"})

        elif sub == "填空题":
            # 格式: 题目（答案1）……（答案2）→ 替换为 ______
            parts = re.split(r'(?:^|\n)(\d+)\.\s*', text)
            for pi in range(1, len(parts)-1, 2):
                q_text = parts[pi+1].strip()
                blanks = re.findall(r'[（(]([^）)]*?)[）)]', q_text)
                q_clean = re.sub(r'[（(][^）)]*?[）)]', '______', q_text)
                questions.append({
                    "q": q_clean,
                    "answer": "、".join(blanks) if blanks else ""
                })

        elif sub == "判断题":
            # 格式: 题目（√）或 题目（×）
            parts = re.split(r'(?:^|\n)(\d+)\.\s*', text)
            for pi in range(1, len(parts)-1, 2):
                q_text = parts[pi+1].strip()
                m = re.search(r'[（(]([×√])[）)]', q_text)
                answer = m.group(1) if m else "?"
                q_clean = re.sub(r'[（(][×√][）)]', '', q_text).strip()
                questions.append({"q": q_clean, "answer": answer})

        elif sub == "简答题":
            # 格式: 题目。答案全文（句号后为答案）
            parts = re.split(r'(?:^|\n)(\d+)\.\s*', text)
            for pi in range(1, len(parts)-1, 2):
                q_text = parts[pi+1].strip()
                m = re.match(r'([^。？：]*[。？：])\s*(.*)', q_text, re.DOTALL)
                if m:
                    q = m.group(1).strip()
                    a = m.group(2).strip()
                else:
                    q = q_text
                    a = ""
                a = a.replace('\n', ' ').replace('\r', '').strip()
                questions.append({"q": q, "answer": a})

        section_data[sub] = questions

    result[sec] = section_data

# 写入 JSON
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# 统计
total = sum(len(vv) for v in result.values() for vv in v.values())
print(f"  解析完成: {total} 题, 保存到 {JSON_PATH}")

# ============================================================
# 第 2 步: 构建 index.html
# ============================================================
print("[2/3] 构建 index.html ...")

# CSS 样式 ====================================================
CSS = r'''
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#f0f2f5;--card:#fff;--primary:#2563eb;--primary-light:#eff6ff;--text:#1e293b;--text2:#64748b;--border:#e2e8f0;--success:#16a34a;--error:#dc2626;--warn:#d97706;--radius:10px;--shadow:0 1px 3px rgba(0,0,0,.08)}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text);min-height:100dvh;-webkit-tap-highlight-color:transparent}
header{position:sticky;top:0;z-index:100;background:var(--card);border-bottom:1px solid var(--border);padding:0 12px}
.header-top{display:flex;align-items:center;gap:8px;padding:10px 0}
.header-top h1{font-size:18px;font-weight:700;white-space:nowrap;color:var(--primary)}
.search-wrap{flex:1;position:relative}
.search-wrap input{width:100%;height:40px;padding:0 12px 0 36px;border:1px solid var(--border);border-radius:20px;font-size:15px;background:var(--bg);outline:none;transition:border-color .2s}
.search-wrap input:focus{border-color:var(--primary)}
.search-wrap svg{position:absolute;left:11px;top:50%;transform:translateY(-50%);width:18px;height:18px;color:var(--text2)}
.mode-toggle{display:flex;background:var(--bg);border-radius:20px;padding:2px;gap:0}
.mode-toggle button{padding:8px 14px;border:none;border-radius:18px;font-size:13px;font-weight:600;cursor:pointer;background:transparent;color:var(--text2);transition:all .2s;white-space:nowrap}
.mode-toggle button.active{background:var(--primary);color:#fff;box-shadow:0 1px 3px rgba(37,99,235,.3)}
.mode-toggle button.exam-btn{background:var(--warn);color:#fff;margin-left:4px}
nav{padding:0 12px}
.section-tabs,.sub-tabs{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;padding:6px 0}
.section-tabs::-webkit-scrollbar,.sub-tabs::-webkit-scrollbar{display:none}
.section-tabs button,.sub-tabs button{flex-shrink:0;padding:6px 14px;border:1px solid var(--border);border-radius:16px;font-size:13px;cursor:pointer;background:var(--card);color:var(--text2);transition:all .15s;white-space:nowrap}
.section-tabs button.active,.sub-tabs button.active{background:var(--primary);color:#fff;border-color:var(--primary)}
.sub-tabs button{font-size:12px;padding:4px 12px}
.info-bar{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;font-size:13px;color:var(--text2)}
main{padding:0 8px 100px}
.card{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:10px;overflow:hidden}
.card-head{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:var(--primary-light);border-bottom:1px solid rgba(37,99,235,.1)}
.card-tag{font-size:11px;font-weight:600;color:var(--primary);padding:2px 8px;background:rgba(37,99,235,.1);border-radius:10px}
.card-num{font-size:11px;color:var(--text2)}
.card-body{padding:14px}
.card-q{font-size:15px;line-height:1.6;color:var(--text);margin-bottom:12px}
.card-a{font-size:14px;line-height:1.6;color:var(--success);background:#f0fdf4;border-radius:8px;padding:10px 14px;margin-top:8px;display:none}
.card-a.visible{display:block}
.card-a .label{font-size:11px;font-weight:600;color:var(--success);margin-bottom:4px;display:block}
.tf-btns{display:flex;gap:10px;margin-top:8px}
.tf-btn{flex:1;padding:14px;border:1.5px solid var(--border);border-radius:var(--radius);font-size:18px;font-weight:700;cursor:pointer;background:var(--card);transition:all .15s}
.tf-btn:active{transform:scale(.97)}
.tf-btn.correct{border-color:var(--success);background:#f0fdf4;color:var(--success)}
.tf-btn.wrong{border-color:var(--error);background:#fef2f2;color:var(--error)}
.reveal-btn{display:inline-flex;align-items:center;gap:6px;margin-top:10px;padding:8px 16px;border:1px solid var(--border);border-radius:20px;font-size:13px;cursor:pointer;background:var(--card);color:var(--text2);transition:all .15s}
.reveal-btn:active{background:var(--bg)}
.empty-state{text-align:center;padding:60px 20px;color:var(--text2)}
.empty-state svg{width:48px;height:48px;margin-bottom:12px;opacity:.3}
#exam-overlay{position:fixed;inset:0;z-index:200;background:var(--bg);display:none;flex-direction:column;overflow-y:auto}
#exam-overlay.active{display:flex}
.exam-head{position:sticky;top:0;z-index:10;background:var(--card);border-bottom:1px solid var(--border);padding:12px 16px;display:flex;align-items:center;justify-content:space-between;gap:8px}
.exam-timer{font-size:20px;font-weight:700;color:var(--primary);font-variant-numeric:tabular-nums}
.exam-timer.warning{color:var(--error);animation:blink 1s infinite}
@keyframes blink{50%{opacity:.4}}
.exam-progress{font-size:13px;color:var(--text2)}
.exam-body{flex:1;padding:12px 8px}
.exam-card{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:12px;padding:16px}
.exam-q-num{font-size:12px;font-weight:600;color:var(--primary);margin-bottom:8px}
.exam-q-text{font-size:15px;line-height:1.6;margin-bottom:12px}
.exam-foot{position:sticky;bottom:0;background:var(--card);border-top:1px solid var(--border);padding:12px 16px;display:flex;gap:8px}
.exam-foot button{flex:1;padding:12px;border:none;border-radius:var(--radius);font-size:15px;font-weight:600;cursor:pointer}
.btn-submit{background:var(--primary);color:#fff}
.btn-cancel{background:var(--bg);color:var(--text2);border:1px solid var(--border)}
.score-overlay{position:fixed;inset:0;z-index:300;background:rgba(0,0,0,.5);display:none;align-items:center;justify-content:center;padding:20px}
.score-overlay.active{display:flex}
.score-card{background:var(--card);border-radius:16px;padding:28px;width:100%;max-width:360px;text-align:center}
.score-num{font-size:48px;font-weight:800;color:var(--primary)}
.score-detail{font-size:14px;color:var(--text2);margin:8px 0 20px}
.score-card button{padding:10px 32px;border:none;border-radius:20px;font-size:14px;font-weight:600;cursor:pointer;background:var(--primary);color:#fff;margin:4px}
.score-card button.btn-outline{background:transparent;color:var(--primary);border:1px solid var(--primary)}
'''

# JavaScript 逻辑 ============================================
JS = r'''
var SUBTYPES=["选择题","填空题","判断题","简答题"];
var SUB_LABELS={"选择题":"选择题","填空题":"填空题","判断题":"判断题","简答题":"简答题"};
var state={mode:"browse",section:null,subtype:null,search:"",exam:null};
var all=[];
for(var s in DATA){for(var t in DATA[s]){DATA[s][t].forEach(function(q,i){all.push({section:s,subtype:t,index:i+1,q:q.q,answer:q.answer});});}}
function filter(){var qs=all;if(state.section)qs=qs.filter(function(q){return q.section===state.section});if(state.subtype)qs=qs.filter(function(q){return q.subtype===state.subtype});if(state.search){var kw=state.search.toLowerCase();qs=qs.filter(function(q){return q.q.toLowerCase().indexOf(kw)>-1||q.answer.toLowerCase().indexOf(kw)>-1})}return qs}
function render(){var qs=filter();document.getElementById("info").textContent=qs.length+" 题";var el=document.getElementById("list");if(!qs.length){el.innerHTML='<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg><div>没有匹配的题目</div></div>';return}var isBrowse=state.mode==="browse";var html="";qs.forEach(function(q,i){var ahtml="";var qd=q.q;if(q.subtype==="选择题"){if(isBrowse)ahtml='<div class="card-a visible"><span class="label">答案</span>'+q.answer+'</div>';else ahtml='<div class="card-a"></div><button class="reveal-btn" data-q="'+i+'">显示答案</button>'}else if(q.subtype==="判断题"){if(isBrowse)ahtml='<div class="card-a visible"><span class="label">答案</span>'+q.answer+'</div>';else ahtml='<div class="tf-btns"><button class="tf-btn" data-q="'+i+'" data-val="√">✓</button><button class="tf-btn" data-q="'+i+'" data-val="×">✗</button></div><div class="card-a"></div>'}else if(q.subtype==="填空题"){qd=q.q.replace(/______/g,'<span style="display:inline-block;min-width:40px;border-bottom:2px solid var(--primary);margin:0 4px;text-align:center">___</span>');if(isBrowse)ahtml='<div class="card-a visible"><span class="label">答案</span>'+q.answer+'</div>';else ahtml='<div class="card-a"></div><button class="reveal-btn" data-q="'+i+'">显示答案</button>'}else{if(isBrowse)ahtml='<div class="card-a visible"><span class="label">答案</span>'+q.answer+'</div>';else ahtml='<div class="card-a"></div><button class="reveal-btn" data-q="'+i+'">显示答案</button>'}var sl=SUB_LABELS[q.subtype]||q.subtype;html+='<div class="card"><div class="card-head"><span class="card-tag">'+q.section+' · '+sl+'</span><span class="card-num">#'+q.index+'</span></div><div class="card-body"><div class="card-q">'+qd+'</div>'+ahtml+'</div></div>'});el.innerHTML=html;if(state.mode==="practice"){el.querySelectorAll(".tf-btn").forEach(function(b){b.addEventListener("click",function(){if(this.parentElement.querySelector(".correct,.wrong"))return;var qi=parseInt(this.dataset.q);var q=qs[qi];if(this.dataset.val===q.answer)this.classList.add("correct");else{this.classList.add("wrong");this.parentElement.querySelector('[data-val="'+q.answer+'"]').classList.add("correct")}this.parentElement.querySelectorAll(".tf-btn").forEach(function(x){x.style.pointerEvents="none"});var c=this.closest(".card");var a=c.querySelector(".card-a");if(a){a.innerHTML='<span class="label">答案</span>'+q.answer;a.classList.add("visible")}})});el.querySelectorAll(".reveal-btn").forEach(function(b){b.addEventListener("click",function(){var qi=parseInt(this.dataset.q);var q=qs[qi];var c=this.closest(".card");var a=c.querySelector(".card-a");if(a){a.innerHTML='<span class="label">答案</span>'+q.answer;a.classList.add("visible")}this.remove()})})}}
function initTabs(){var st=document.getElementById("secTabs");var sb=document.getElementById("subTabs");st.innerHTML='<button class="active" data-sec="">全部</button>'+SECTIONS.map(function(s){return'<button data-sec="'+s+'">'+s+'</button>'}).join("");sb.innerHTML='<button class="active" data-sub="">全部</button>'+SUBTYPES.map(function(s){return'<button data-sub="'+s+'">'+SUB_LABELS[s]+'</button>'}).join("");st.querySelectorAll("button").forEach(function(b){b.addEventListener("click",function(){st.querySelectorAll("button").forEach(function(x){x.classList.remove("active")});this.classList.add("active");state.section=this.dataset.sec||null;render();this.scrollIntoView({behavior:"smooth",block:"nearest",inline:"center"})})});sb.querySelectorAll("button").forEach(function(b){b.addEventListener("click",function(){sb.querySelectorAll("button").forEach(function(x){x.classList.remove("active")});this.classList.add("active");state.subtype=this.dataset.sub||null;render()})})}
document.getElementById("btnBrowse").addEventListener("click",function(){state.mode="browse";document.getElementById("btnBrowse").classList.add("active");document.getElementById("btnPractice").classList.remove("active");render()});
document.getElementById("btnPractice").addEventListener("click",function(){state.mode="practice";document.getElementById("btnPractice").classList.add("active");document.getElementById("btnBrowse").classList.remove("active");render()});
document.getElementById("search").addEventListener("input",function(){state.search=this.value.trim();render()});
var examTimer=null;
document.getElementById("btnExam").addEventListener("click",function(){var qs=filter();if(!qs.length){alert("当前筛选条件下没有题目");return}var n=Math.min(20,qs.length);var sel=[].concat(qs).sort(function(){return Math.random()-.5}).slice(0,n);startExam(sel)});
function startExam(qs){state.exam={questions:qs,answers:new Array(qs.length).fill(null),startTime:Date.now(),duration:30*60,current:0};document.getElementById("exam-overlay").classList.add("active");document.body.style.overflow="hidden";renderExam();startTimer()}
function startTimer(){clearInterval(examTimer);var te=document.getElementById("examTimer");examTimer=setInterval(function(){var e=Math.floor((Date.now()-state.exam.startTime)/1000);var r=Math.max(0,state.exam.duration-e);var m=Math.floor(r/60);var s=r%60;te.textContent=m+":"+(s<10?"0":"")+s;if(r<300)te.classList.add("warning");else te.classList.remove("warning");if(r<=0)submitExam()},1000)}
function renderExam(){var ex=state.exam;if(!ex)return;document.getElementById("examProgress").textContent=(ex.current+1)+"/"+ex.questions.length;var q=ex.questions[ex.current];var a=ex.answers[ex.current];var ah="";if(q.subtype==="选择题"){ah='<div style="margin-top:10px"><textarea style="width:100%;min-height:60px;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:14px;resize:vertical;font-family:inherit" placeholder="输入你的答案..." oninput="examAnswerText(this.value)">'+(a||"")+'</textarea></div>'}else if(q.subtype==="判断题"){ah='<div class="tf-btns"><button class="tf-btn'+(a==='√'?' selected':'')+'" onclick="examAnswer(\'√\')">✓</button><button class="tf-btn'+(a==='×'?' selected':'')+'" onclick="examAnswer(\'×\')">✗</button></div>'}else{ah='<div style="margin-top:10px"><textarea style="width:100%;min-height:80px;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:14px;resize:vertical;font-family:inherit" placeholder="输入你的答案..." oninput="examAnswerText(this.value)">'+(a||"")+'</textarea></div>'}document.getElementById("examBody").innerHTML='<div class="exam-card"><div class="exam-q-num">'+q.section+' · '+q.subtype+' #'+q.index+'</div><div class="exam-q-text">'+q.q+'</div>'+ah+'</div>';document.getElementById("exam-overlay").scrollTop=0}
function examAnswer(v){if(!state.exam)return;state.exam.answers[state.exam.current]=v;renderExam()}
function examAnswerText(v){if(!state.exam)return;state.exam.answers[state.exam.current]=v}
function examPrev(){if(!state.exam)return;if(state.exam.current>0){state.exam.current--;renderExam()}}
function examNext(){if(!state.exam)return;if(state.exam.current<state.exam.questions.length-1){state.exam.current++;renderExam()}}
function submitExam(){clearInterval(examTimer);var ex=state.exam;if(!ex)return;var c=0;ex.questions.forEach(function(q,i){var ua=ex.answers[i];var ok=false;if(q.subtype==="选择题")ok=ua&&(q.answer.indexOf(ua.trim())>-1||ua.trim().indexOf(q.answer)>-1);else if(q.subtype==="判断题")ok=ua===q.answer;else if(ua&&ua.trim())ok=q.answer.indexOf(ua.trim())>-1||ua.trim().indexOf(q.answer)>-1;if(ok)c++});var sc=Math.round((c/ex.questions.length)*100);document.getElementById("scoreNum").textContent=sc+"%";document.getElementById("scoreDetail").textContent="正确 "+c+"/"+ex.questions.length+" 题";document.getElementById("scoreOverlay").classList.add("active")}
function closeScore(){document.getElementById("scoreOverlay").classList.remove("active");closeExam()}
function viewAnswers(){document.getElementById("scoreOverlay").classList.remove("active");var ex=state.exam;if(!ex)return;var h="";ex.questions.forEach(function(q,i){var ua=ex.answers[i]||"未作答";var ok=false;if(q.subtype==="选择题")ok=ua&&(q.answer.indexOf(ua.trim())>-1||ua.trim().indexOf(q.answer)>-1);else if(q.subtype==="判断题")ok=ua===q.answer;else ok=ua&&(q.answer.indexOf(ua.trim())>-1||ua.trim().indexOf(q.answer)>-1);h+='<div class="exam-card"><div class="exam-q-num" style="color:'+(ok?'var(--success)':'var(--error)')+'">'+q.section+' · '+q.subtype+' #'+q.index+' '+(ok?'✓':'✗')+'</div><div class="exam-q-text">'+q.q+'</div><div style="font-size:13px;color:var(--text2);margin-bottom:4px">你的答案: '+ua+'</div><div style="font-size:13px;color:var(--success)">正确答案: '+q.answer+'</div></div>'});document.getElementById("examBody").innerHTML=h;document.getElementById("examFoot").innerHTML='<button class="btn-submit" onclick="closeExam()">返回</button>';document.getElementById("exam-overlay").scrollTop=0}
function closeExam(){clearInterval(examTimer);document.getElementById("exam-overlay").classList.remove("active");document.getElementById("scoreOverlay").classList.remove("active");document.body.style.overflow="";state.exam=null;document.getElementById("examFoot").innerHTML='<button class="btn-cancel" onclick="closeExam()">退出</button><button class="btn-submit" onclick="submitExam()">交卷</button>';render()}
initTabs();render();
'''

# 组装 HTML ==================================================
with open(JSON_PATH, encoding="utf-8") as f:
    data = json.load(f)

data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
sections_json = json.dumps(list(data.keys()), ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>综合题库</title>
<style>{CSS}</style>
</head>
<body>
<header>
<div class="header-top">
<h1>题库</h1>
<div class="search-wrap">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
<input type="search" id="search" placeholder="搜索题目...">
</div>
<div class="mode-toggle">
<button id="btnBrowse" class="active">浏览</button>
<button id="btnPractice">练习</button>
<button id="btnExam" class="exam-btn">考试</button>
</div>
</div>
</header>
<nav>
<div class="section-tabs" id="secTabs"></div>
<div class="sub-tabs" id="subTabs"></div>
</nav>
<div class="info-bar"><span id="info"></span></div>
<main id="list"></main>

<div id="exam-overlay">
<div class="exam-head">
<button class="btn-cancel" onclick="closeExam()" style="flex:none;padding:8px 16px;font-size:13px">退出</button>
<div><span class="exam-timer" id="examTimer">30:00</span></div>
<div class="exam-progress" id="examProgress">0/0</div>
<div style="display:flex;gap:6px">
<button class="btn-cancel" onclick="examPrev()" style="padding:8px 12px;font-size:13px">上一题</button>
<button class="btn-cancel" onclick="examNext()" style="padding:8px 12px;font-size:13px">下一题</button>
</div>
</div>
<div class="exam-body" id="examBody"></div>
<div class="exam-foot" id="examFoot">
<button class="btn-cancel" onclick="closeExam()">退出</button>
<button class="btn-submit" onclick="submitExam()">交卷</button>
</div>
</div>

<div class="score-overlay" id="scoreOverlay">
<div class="score-card">
<div style="font-size:12px;font-weight:600;color:var(--primary);margin-bottom:8px">模拟考试成绩</div>
<div class="score-num" id="scoreNum">0%</div>
<div class="score-detail" id="scoreDetail"></div>
<button onclick="closeScore()">返回</button>
<button class="btn-outline" onclick="viewAnswers()">查看答案</button>
</div>
</div>

<script>
var DATA={data_json};
var SECTIONS={sections_json};
{JS}
</script>
</body>
</html>'''

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"  构建完成: {HTML_PATH} ({len(html)//1024} KB)")

# ============================================================
# 第 3 步: 完成
# ============================================================
print("[3/3] 完成！")
print(f"  题库.json: {total} 题结构数据")
print(f"  index.html: 单页应用，浏览器直接打开即可使用")
