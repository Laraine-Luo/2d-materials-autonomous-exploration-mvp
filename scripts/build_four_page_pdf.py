"""Build a four-page internal competition-layout proof and verify page count separately."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/pdf/开放探索赛题_问题定义文档_二维材料AI自主探索环境.pdf"
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"


NAVY = colors.HexColor("#153B5B")
TEAL = colors.HexColor("#0E7490")
PALE = colors.HexColor("#E9F7FA")
PALE_BLUE = colors.HexColor("#EEF5FA")
MUTED = colors.HexColor("#667085")


def add_box(d, x, y, w, h, title_text, detail_text="", fill=PALE):
    d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=fill, strokeColor=colors.HexColor("#75B7C8"), strokeWidth=0.8))
    d.add(String(x + w/2, y + h - 14, title_text, fontName="CJK", fontSize=8.5, fillColor=NAVY, textAnchor="middle"))
    if detail_text:
        d.add(String(x + w/2, y + 9, detail_text, fontName="CJK", fontSize=6.7, fillColor=MUTED, textAnchor="middle"))


def add_arrow(d, x1, y1, x2, y2, color=TEAL):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.2))
    if abs(x2-x1) >= abs(y2-y1):
        s = 1 if x2 >= x1 else -1
        d.add(Polygon([x2, y2, x2-6*s, y2+3.5, x2-6*s, y2-3.5], fillColor=color, strokeColor=color))
    else:
        s = 1 if y2 >= y1 else -1
        d.add(Polygon([x2, y2, x2-3.5, y2-6*s, x2+3.5, y2-6*s], fillColor=color, strokeColor=color))


def research_gap_figure():
    d = Drawing(500, 112)
    d.add(String(6, 96, "图1  从数据积累到可评审自主探索环境", fontName="CJK", fontSize=8, fillColor=TEAL))
    boxes = [(8,"数据库积累","结构与计算性质"),(132,"性质预测","单次模型输出"),(256,"现有缺口","流程／预算／发现标准"),(380,"本项目环境","预测—选择—反馈")]
    for idx, (x,t,detail) in enumerate(boxes):
        add_box(d,x,35,105,43,t,detail,colors.HexColor("#FFF5E8") if idx==2 else PALE)
        if idx < len(boxes)-1:
            add_arrow(d,x+105,56,x+124,56)
    d.add(String(250, 15, "问题不在“是否有数据库”，而在如何形成可复查的序贯探索与评价闭环", fontName="CJK", fontSize=7.2, fillColor=NAVY, textAnchor="middle"))
    return d


def oaf_figure():
    d = Drawing(500, 128)
    d.add(String(6, 112, "图2  Observation—Action—Feedback有限预算闭环", fontName="CJK", fontSize=8, fillColor=TEAL))
    add_box(d,10,45,86,43,"候选池","合格MP ID")
    add_box(d,112,45,86,43,"观察","预测／不确定性／历史")
    add_box(d,214,45,86,43,"行动","选择下一MP ID",colors.HexColor("#FFF5E8"))
    add_box(d,316,45,86,43,"环境反馈","MP性质／误差／信号")
    add_box(d,418,45,72,43,"更新","模型＋日志")
    for x in (96,198,300,402):
        add_arrow(d,x,66,x+16,66)
    d.add(Line(454,45,454,24,strokeColor=TEAL,strokeWidth=1.2))
    d.add(Line(454,24,155,24,strokeColor=TEAL,strokeWidth=1.2))
    add_arrow(d,155,24,155,45)
    d.add(String(305, 10, "每次查询消耗1单位预算；Static冻结模型，Iterative在反馈后重训", fontName="CJK", fontSize=7, fillColor=NAVY, textAnchor="middle"))
    return d


def evidence_gate_figure():
    d = Drawing(500, 142)
    d.add(String(6, 126, "图3  MoS2索引记录进入正式候选池的证据门控", fontName="CJK", fontSize=8, fillColor=TEAL))
    steps=[(8,"公式层索引","MoS2 → 12个MP ID"),(132,"官方API","身份／版本／性质"),(256,"双重审核","二维性＋计算方法"),(380,"正式候选","训练／查询资格")]
    for idx,(x,t,detail) in enumerate(steps):
        add_box(d,x,65,105,43,t,detail,PALE_BLUE if idx!=2 else colors.HexColor("#FFF5E8"))
        if idx<len(steps)-1:
            add_arrow(d,x+105,86,x+124,86)
    d.add(Line(308,65,308,39,strokeColor=colors.HexColor("#C2410C"),strokeWidth=1.2))
    add_arrow(d,308,39,308,34,colors.HexColor("#C2410C"))
    add_box(d,248,0,120,34,"审核／字段未通过","保留护照，不训练",colors.HexColor("#FEF0EC"))
    d.add(String(250, 119, "任一门控失败即停止；网页数值命中不自动成为D1/D2", fontName="CJK", fontSize=7.1, fillColor=NAVY, textAnchor="middle"))
    return d


def validation_result_figure():
    """Compact cumulative-discovery figure from the frozen Run 43 summary."""
    d = Drawing(500, 150)
    d.add(String(6, 134, "图3  24条独立MX2候选中的累计D2信号（20个共同种子均值）", fontName="CJK", fontSize=8, fillColor=TEAL))
    left, bottom, width, height = 46, 28, 400, 88
    d.add(Line(left, bottom, left, bottom + height, strokeColor=MUTED, strokeWidth=0.7))
    d.add(Line(left, bottom, left + width, bottom, strokeColor=MUTED, strokeWidth=0.7))
    for tick in range(0, 6):
        y = bottom + height * tick / 5
        d.add(Line(left, y, left + width, y, strokeColor=colors.HexColor("#E4E7EC"), strokeWidth=0.35))
        d.add(String(left - 8, y - 2, str(tick), fontName="CJK", fontSize=6.5, fillColor=MUTED, textAnchor="end"))
    for q in range(1, 9):
        x = left + width * (q - 1) / 7
        d.add(String(x, bottom - 12, str(q), fontName="CJK", fontSize=6.5, fillColor=MUTED, textAnchor="middle"))
    series = {
        "Random 2.60": ([0.25,0.45,0.85,1.40,1.85,2.20,2.40,2.60], colors.HexColor("#98A2B3")),
        "Static 3.85": ([0.20,0.45,1.20,1.90,1.90,2.00,2.95,3.85], colors.HexColor("#2563EB")),
        "Iterative w=.35 3.40": ([0.00,0.05,0.40,0.95,1.50,2.10,2.75,3.40], colors.HexColor("#0E7490")),
        "诊断 w=.15 4.70": ([0.00,0.25,0.90,1.80,2.70,3.35,4.10,4.70], colors.HexColor("#EA580C")),
    }
    legend_x = 52
    for idx, (label, (values, color)) in enumerate(series.items()):
        pts = []
        for q, value in enumerate(values):
            pts.extend([left + width * q / 7, bottom + height * value / 5])
        for j in range(0, len(pts) - 2, 2):
            d.add(Line(pts[j], pts[j+1], pts[j+2], pts[j+3], strokeColor=color, strokeWidth=1.6))
        d.add(Line(legend_x, 11, legend_x + 14, 11, strokeColor=color, strokeWidth=2))
        d.add(String(legend_x + 18, 8.5, label, fontName="CJK", fontSize=6.4, fillColor=NAVY))
        legend_x += 108
    d.add(String(12, 73, "累计D2", fontName="CJK", fontSize=6.5, fillColor=MUTED, angle=90, textAnchor="middle"))
    d.add(String(460, 16, "查询预算", fontName="CJK", fontSize=6.5, fillColor=MUTED))
    return d


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("CJK", 7)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(14 * mm, 8 * mm, "面向二维材料电子性质发现的AI自主探索环境 · 初赛提交版")
    canvas.drawRightString(196 * mm, 8 * mm, f"{doc.page}/4")
    canvas.restoreState()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("CJK", FONT))
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title-cn", parent=styles["Title"], fontName="CJK", fontSize=17, leading=21, alignment=TA_CENTER, textColor=colors.HexColor("#153B5B"), spaceAfter=5)
    subtitle = ParagraphStyle("subtitle-cn", parent=title, fontSize=11, leading=14, textColor=colors.HexColor("#35627F"), spaceAfter=9)
    h1 = ParagraphStyle("h1-cn", parent=styles["Heading1"], fontName="CJK", fontSize=12, leading=15, textColor=colors.HexColor("#0E7490"), spaceBefore=5, spaceAfter=4)
    h2 = ParagraphStyle("h2-cn", parent=styles["Heading2"], fontName="CJK", fontSize=10.3, leading=13, textColor=colors.HexColor("#153B5B"), spaceBefore=4, spaceAfter=3)
    body = ParagraphStyle("body-cn", parent=styles["BodyText"], fontName="CJK", fontSize=8.35, leading=11.55, textColor=colors.HexColor("#202A33"), spaceAfter=3.5, wordWrap="CJK")
    small = ParagraphStyle("small-cn", parent=body, fontSize=7.7, leading=10.2, textColor=colors.HexColor("#475467"))
    callout = ParagraphStyle("callout-cn", parent=body, fontSize=8.4, leading=11.5, borderColor=colors.HexColor("#9DD8E8"), borderWidth=0.6, borderPadding=5, backColor=colors.HexColor("#F2FAFC"), spaceBefore=4, spaceAfter=5)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=13*mm, rightMargin=13*mm, topMargin=11*mm, bottomMargin=13*mm, title="面向二维材料电子性质发现的AI自主探索环境")
    story = []

    story += [Paragraph("面向二维材料电子性质发现的AI自主探索环境", title), Paragraph("——基于Band Gap预测与迭代搜索的材料发现框架", subtitle), Paragraph("一、问题与证据", h1)]
    story += [Paragraph("1.1 真实问题或需求", h2), Paragraph("当前二维材料数据库（如Materials Project、C2DB）已经积累了大量结构信息与计算性质数据，为材料发现提供了丰富的数据基础[1–2]。然而，在大规模二维材料候选空间中，如何高效探索满足目标电子性质与稳定性约束的材料候选仍然是一个重要挑战。现有机器学习模型虽然能够实现材料性质预测，但预测结果通常作为静态筛选依据，尚未充分形成“预测—选择—反馈—再探索”的动态闭环过程，限制了模型在复杂材料搜索任务中的应用效率。", body), Paragraph("因此，本项目拟探索构建基于机器学习预测与迭代搜索机制的二维材料自主探索环境，使Agent能够根据预测结果、不确定性反馈以及历史探索记录动态调整搜索策略，在有限计算资源下优化候选材料探索过程，并筛选具有目标Band Gap性质且满足稳定性约束的二维材料候选。", body)]
    story += [Paragraph("1.2 为什么尚未被结构化", h2), Paragraph("近年来，机器学习、主动学习和优化算法已经被应用于材料性质预测与候选筛选任务，并在降低高通量计算成本方面取得了一定进展。然而，现有方法通常针对特定材料体系、性质目标或优化流程进行设计，探索、反馈和评价标准往往与具体任务高度绑定，尚未形成针对特定二维材料电子性质发现任务、具有统一探索流程和评价标准的自主探索环境。", body), Paragraph("二维材料候选空间具有高维、离散和复杂结构-性质关系等特点。对于目标电子性质的发现任务，智能系统不仅需要预测材料性质，还需要综合考虑预测性能、不确定性、稳定性约束以及历史探索结果，动态决定下一步探索方向。目前，如何定义一个能够支持Agent持续探索、获得反馈并优化搜索策略的二维材料发现环境，仍缺少统一的问题定义和评价体系。", body), Paragraph("因此，该问题尚未被充分结构化为一个可由智能体持续迭代解决的科学探索任务。", body)]
    story += [Paragraph("1.3 研究价值与合适切片", h2), Paragraph("二维材料因其独特电子性质，在半导体、光电器件和能源材料等领域具有重要应用潜力。然而，传统基于DFT的材料筛选流程受到计算成本限制，难以快速覆盖不断扩大的候选空间。因此，探索更加高效的智能化材料发现流程，对于提升计算材料研究效率具有重要意义。", body), Paragraph("本项目不试图解决完整的新材料研发流程，而是聚焦于二维材料发现中的一个具体环节：在已有数据库和计算数据基础上，通过AI自主探索策略研究如何高效搜索满足目标Band Gap和稳定性约束的二维材料候选空间。AI在该问题中的价值不只是替代单次性质预测，而是提供面向探索过程的搜索、归纳和优化能力。具体而言，Agent可以：", body), Paragraph("1. 利用机器学习模型学习已有材料结构与电子性质之间的关系；<br/>2. 根据预测结果和模型不确定性选择下一批具有探索价值的候选材料；<br/>3. 根据反馈结果不断更新搜索策略，形成“预测—探索—反馈”的闭环过程。", body), Paragraph("通过构建这一小规模自主探索环境，可以研究不同搜索策略在二维材料发现任务中的有效性，并分析哪些材料结构特征与电子性质之间存在可解释关联，为未来更复杂的AI驱动材料发现流程提供方法基础。", body), Paragraph("证据链：数据库积累 → 性质预测 → 统一探索接口、预算、日志和发现评价缺口 → 本项目可运行自主探索环境", callout), research_gap_figure()]
    story.append(PageBreak())

    story += [Paragraph("二、环境接口", h1), Paragraph("2.1 固定规则", h2), Paragraph("正式科学数据仅来自Materials Project；160条随机记录只验证软件闭环。候选主键为MP ID，MoS2索引层级为Materials Explorer → Mo-S → MoS2 → mp-id。一次运行冻结数据库版本、计算方法队列、候选池、目标区间、初始样本、预算和随机种子。", body)]
    rule_data = [["固定项","设定"],["目标性质","Band Gap 1.5—2.5 eV"],["稳定性","Formation Energy≤-0.2 eV/atom，且E_hull≤0.1或is_stable"],["开发／验证","7条MoS2已知标签；24条跨化学式MX2独立验证"],["预算","每策略8次顺序查询；16条标签保持未揭示；20个共同种子"],["隔离","非API、uncertain_2d、方法不一致、跨版本记录"]]
    t=Table(rule_data,colWidths=[35*mm,137*mm]); t.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"CJK"),("FONTSIZE",(0,0),(-1,-1),7),("LEADING",(0,0),(-1,-1),9),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DFF3F8")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#B8C4CC")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4)])); story += [t,Spacer(1,3)]
    story += [Paragraph("阈值是MVP预注册评价规则，不等于普遍可合成判据；真实MP值只被筛选和评价，不被简单函数生成或校正。24条经人工批准用于验证，mp-1120746因方法不一致继续隔离，验证记录不得用于初始训练。", small), Paragraph("2.2 观察／行动／反馈", h2), Paragraph("观察：候选身份与结构特征、预测值、不确定性、稳定性、审核状态、历史与预算，但不含验证Band Gap。行动：选择下一MP ID。反馈：环境查询后才揭示MP Band Gap，返回误差、D0—D2信号与预算消耗。Random均匀抽样；Static Top-N冻结初始排序；Iterative用12个Bootstrap岭模型估计均值与离散度，最大化A(x)=0.65T(ŷ)+0.35u/max(u)，并在反馈后重训[3]。", body), Paragraph("闭环：候选池 → 预测与不确定性 → 策略选择MP ID → 揭示MP反馈 → 信号／日志 → 更新模型与下一轮", callout), Paragraph("2.3 记录与预算", h2), Paragraph("每轮记录轮次、策略、MP ID、预测、不确定性、MP反馈、三项稳定性、选择理由、误差、发现等级、规则版本、人工复核和预算位置。探索状态统一使用exploration_status_前缀。正式验证采用8次单条查询并保留16条未揭示；标签存于Git忽略oracle，公开护照只保存承诺哈希；密钥和原始响应不上传[4]。", body), Spacer(1,5), oaf_figure()]
    story.append(PageBreak())

    story += [Paragraph("三、发现信号与参照", h1), Paragraph("3.1 什么算发现", h2)]
    sig_data=[["等级","证据含义","当前证据与判定边界"],["D0","可追踪的技术／索引事件","已实现；只证明流程可追踪"],["D1","真实MP Band Gap落入目标区间","已实现；只称“数值命中”"],["D2","D1＋身份、二维性、稳定性、方法与质量审核","已实现；可称“已审核候选信号”"],["D3","在独立留出或重复运行中稳定复现的规律／负结果","本轮仅主张跨MX2负向策略信号"],["D4","高精度计算、独立数据、文献或实验外部验证","未达到；不声明发现新材料"]]
    t=Table(sig_data,colWidths=[14*mm,91*mm,67*mm]); t.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"CJK"),("FONTSIZE",(0,0),(-1,-1),6.65),("LEADING",(0,0),(-1,-1),8.5),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DFF3F8")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#B8C4CC")),("VALIGN",(0,0),(-1,-1),"TOP") ])); story += [t,Spacer(1,3),Paragraph("判定原则：等级不是对同一结果的不同称呼，而是逐级增加证据要求。单条查询最高自动到D2；D3必须来自预注册重复／独立验证；D4必须具有外部验证。异常：|预测Band Gap－MP Band Gap| > max(0.6 eV, 2×不确定性)时进入人工审核。", body),Paragraph("3.2 平凡解／随机／无干预", h2)]
    base_data=[["策略","角色","20种子平均D2/8","命中率"],["Random","必需基线","2.60","32.50%"],["Static Top-N","必需基线","3.85","48.13%"],["Iterative w=.35","预注册主策略","3.40","42.50%"],["Iterative w=.15","仅诊断","4.70","58.75%"]]
    t=Table(base_data,colWidths=[42*mm,52*mm,43*mm,35*mm]); t.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"CJK"),("FONTSIZE",(0,0),(-1,-1),7),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DFF3F8")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#B8C4CC")),("ALIGN",(2,1),(-1,-1),"CENTER") ])); story += [t,Spacer(1,3),Paragraph("主策略相对Random为+0.80 D2，配对Bootstrap 95%区间[0.10,1.60]；相对Static为-0.45，区间[-0.90,0.00]。它超过随机但未超过静态基线，故不满足双基线正向门槛。w=.15虽描述性最佳，但属于预注册诊断消融，不能事后替换主策略。结果登记为限定于本MX2队列的D3负向信号。", callout),Paragraph("3.3 最低成功与失败标准", h2),Paragraph("正向D3：至少20个预注册共同种子，主策略平均D2同时高于两个基线至少10%，且两组成对95%区间均在0以上。负向D3：相对任一必需基线的区间上界低于10%最低有意义增益。本轮正向失败、负向通过；版本／方法混合、标签泄漏或离群点驱动仍须作废。", body), validation_result_figure()]
    story.append(PageBreak())

    story += [Paragraph("四、最小验证计划", h1), Paragraph("4.1 一次试跑怎么做", h2), Paragraph("固定版本MP查询 → 稳定性／二维性／方法门控 → MoS2开发闭环 → 冻结MX2独立来源 → 人工签署24＋1 → 标签隔离 → 预注册预算和策略 → 20种子正式验证。", callout), Paragraph("MP数据库版本2026.04.13。25/25结构与方法链解析；12条算法分歧记录均获Robocrys二维支持。项目所有者批准24条进入验证，mp-1120746继续隔离，验证训练合格0条。正式试跑以7条MoS2为初始知识、24条跨化学式MX2为独立候选；每策略查询8条、保留16条未揭示，全部运行无稳定性违规。", body), Paragraph("结果说明：主策略比随机多0.80个D2，却比Static少0.45个；说明当前简单不确定性权重能够增加探索，但尚未把探索收益转化为超过强静态排序的发现效率。诊断w=.15形成下一独立队列的预注册假设，而不是本轮胜者。", callout), Paragraph("4.2 主要风险与失败路径", h2)]
    risk_data=[["风险","检测","处理"],["API／网络失败","响应和错误类型","停止映射，保留审计"],["版本漂移","版本唯一性","整批隔离并重新冻结"],["方法混合","origins＋thermo run_type","进入方法审核队列"],["非二维记录","MP ID级结构审核","不训练，保留偏离统计"],["Band Gap代理误差","异常阈值／留出误差","人工审核，不直接回流"],["数据泄漏","隐藏标签与日志回放","该轮评价作废"],["小样本偶然性","多种子与置信区间","未达门槛报告失败"],["无证据批准","审核者／时间／理由","禁止晋级"]]
    t=Table(risk_data,colWidths=[42*mm,58*mm,72*mm]); t.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"CJK"),("FONTSIZE",(0,0),(-1,-1),6.7),("LEADING",(0,0),(-1,-1),8.4),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DFF3F8")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#B8C4CC")),("VALIGN",(0,0),(-1,-1),"TOP") ])); story += [t,Spacer(1,3),Paragraph("4.3 复现与开源计划", h2),Paragraph("公开代码、配置、字段映射、MP索引清单、护照、三条主对照及两条诊断策略、逐轮日志、汇总和自动测试；160条夹具明确无科学依据。MP数据记录版本、查询和CC BY 4.0许可；密钥、账号、原始本地响应、oracle标签和虚拟环境不上传。正式API固定mp-api==0.46.4与Python 3.11+；持有MP密钥者可重新采集。", body),Paragraph("参考文献：[1] Horton et al., Nat. Mater. 24, 1522–1532 (2025), DOI:10.1038/s41563-025-02272-0；[2] Gjerding et al., 2D Mater. 8, 044002 (2021), DOI:10.1088/2053-1583/ac1059；[3] Lookman et al., npj Comput. Mater. 5, 21 (2019), DOI:10.1038/s41524-019-0153-8；[4] Materials Project API文档；[5] Materials Project Electronic Structure方法说明。", small), Spacer(1,5), evidence_gate_figure()]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build()
