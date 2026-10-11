"""Create a bounded review packet from traceable proposals; create no decisions."""

import argparse
import json
import shutil
from pathlib import Path

from audit_corrected_source_gate import digest, read


def build(root, report):
    papers = {a: read(report / f"paper-{a.lower()}.json") for a in "AB"}
    ledger = read(root / "evals/reviews/dual-paper/HUMAN_SOURCE_REVIEW.json")
    old_events = {e["decision_id"]: e for e in ledger["decisions"]}
    runtime = root / ".runtime/gate-a-reconciliation-20261011"
    for source, target in [
        ("browser-public/results.json", "public-browser.json"),
        ("browser-dual/results.json", "browser.json"),
    ]:
        shutil.copyfile(runtime / source, report / target)
    equivalence = [
        "# 等价性映射待确认清单",
        "",
        "这是独立的技术证明及绑定提案，没有创建 HUMAN_SOURCE_REVIEW 决定。",
        "当前对象 ID、版本、证据指纹及完整新旧原文见 paper-a.json / paper-b.json。",
        "E0 只确认迁移方式：原文、类型、定位一致时按映射引用原决定及原范围；保留 REVISE / REJECT、解释性修订和未解决项，不转换为 ACCEPT，不产生科学 VERIFIED。",
        "现有冻结协议没有自动等价绑定流程，因此本提案尚未生效。公式局部化的历史接受不等于公式重构或科学有效性接受。",
        "",
        "| 论文 | 当前对象 ID | 历史决定 ID | 原决定 | 标题变化 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for letter, d in papers.items():
        by_id = {m.get("new_node_id"): m for m in d["graph_node_mapping"]}
        for p in d["prediction_mapping"]:
            if p["category"] != "NONMATERIAL_METADATA_CHANGE":
                continue
            m = by_id[p["node_id"]]
            heading = (
                ", ".join(m["equivalence_proof"]["literal_heading_removed"]) or "无"
            )
            equivalence.append(
                f"| {letter} | {p['node_id']} | {p['previous_decision_id']} | {p['previous_decision']} | {heading} |"
            )
    equivalence += [
        "",
        "21 项数量的原始源文本、页码、offset 与 bbox 均一致，逐项映射在 quantity_mapping，历史数值/单位/上下文不改。",
        "9 个已评审解析异常实例保留原始 source span，原错误 SECTION 已移除，逐项见 parser_anomaly_mapping。",
        "35 项窗口候选的等价范围限原文归属、原类型和定位；仍需确认的类型、分组、符号修订见 TARGETED-REVIEW.md。",
    ]
    (report / "EQUIVALENCE-PROPOSAL.md").write_text(
        "\n".join(equivalence) + "\n", encoding="utf-8"
    )
    analysis = [
        "# 候选级失败原因",
        "",
        "冻结 precision 定义：没有独立判定的预测不计正确。旧预测表只按 type + 原文生成的哈希键匹配。键失配不能证明科学错误。以下保留实际键、对象 ID、原文及定位。",
        "",
        "| 项目 | 当前原始模型比较 | 当前人工 precision |",
        "| --- | --- | --- |",
        "| A | 16/21 = 76.19% | 未计算；需要等价绑定与局部决定 |",
        "| B | 17/18 = 94.44% | 未计算；需要等价绑定与局部决定 |",
        "",
        "不会通过修改冻结 prediction-review / gold 或删掉有效候选改变这些历史比较。新的人类源归属评估须单独记录当前键的判定，采用相同窗口与阈值。",
    ]
    for letter, d in papers.items():
        for p in d["prediction_mapping"]:
            if not p["why_counted_incorrect"]:
                continue
            analysis += [
                "",
                f"## {letter} / {p['type']} / {p['node_id']}",
                "",
                f"预测键：`{p['prediction_key']}`；PDF 第 {p['page']} 页；bbox `{p['bbox']}`。",
                f"分类：{p['category']}；旧决定：{p['previous_decision_id'] or '无当前对象决定'}。",
                p["why_counted_incorrect"],
                "",
                "```text",
                p["text"],
                "```",
            ]
    analysis += [
        "",
        "A 未召回 a-limitation：历史决定 human-source-A-a-limitation-2 明确 REJECT 为独立对象。原文仍完整保留为背景；冻结 gold 不删，16/17 召回率保持。此项无需重新问用户。",
        "A 旧 PROCESS 汇总确有分组缺陷：包含 PL/Raman 光谱、激光功率与电阻表征整段。通用 v5 改为明确制备/处理原句的编译，遇到可能的小节标签分组，跨块断句保留原文延续。旧汇总保留在 production-corrections-20261011-r2；当前分组是 AI_INTERPRETATION，不暗示完整工艺顺序。",
        "A 新增 METHOD 的 120/200 °C 转移与 12 h 聚合物去除均有原文证据；不能因没有冻结键而删去。关系句由 METHOD 改为 RELATIONSHIP_ANALYSIS，与既有人工要求一致，但当前新类型仍需显式确认。",
        "B SIMULATION 不是全新科学陈述：旧 human-source-B-b-dft-method-1 已 ACCEPT 相同 DFT/VASP/PBE 原文和 SIMULATION 类型，唯一文字变化是前置 DFT calculations 标题分离。无需重复 DFT 内容评审，纳入 E0 等价映射。",
        "B 原图再检查：Sb(0 1 -1 2) 的上划线位于第三个数字 1；Ion/Vth 的 on/th 为下标。浏览器已检查实际独立排版视图；V_th 仍注明此前为模型补充检查。",
        "Equation 1 原始块、页码、定位不变。新 metadata 报告短线/根号/分式解释不确定；没有新增归一化公式、LaTeX 或 VERIFIED。历史 ACCEPT 只在原评审范围内保存，不用它消除该不确定性。冻结 gold/阈值不变；当前人工评估尚不能宣布 PASS。",
    ]
    (report / "CANDIDATE-DELTA.md").write_text(
        "\n".join(analysis) + "\n", encoding="utf-8"
    )
    packet = [
        "# 仅待确认的局部项目",
        "",
        "先确认 E0 等价性绑定提案，不重新评审 35 项等价候选或 21 项数量。E0 不是新的科学 ACCEPT：原历史决定、范围和未解决 REVISE 原样保留。",
        "以下六张卡涉及七个当前对象；A2 把同一源中的工艺汇总和旧氧化子步骤合并呈现，两者决定分别记录。可回复 E0 同意/不同意；A1、A2a、A2b、A3、A4、B1、B2 各 ACCEPT / REVISE / REJECT，并说明需要改动的内容。",
        "所有决定目前为 null；本文件没有替用户作决定。",
        "",
    ]

    def card(tag, letter, p, explanation):
        d = papers[letter]
        m = next(
            m for m in d["graph_node_mapping"] if m.get("new_node_id") == p["node_id"]
        )
        event = old_events.get(p.get("previous_decision_id"))
        packet.extend(
            [
                f"{'###' if tag.startswith('A2b') else '##'} {tag}",
                "",
                explanation,
                "",
                f"旧对象：{m.get('old_node_id', '无同范围的已接受生产对象')}；旧决定：{p.get('previous_decision_id') or '无'} / {p.get('previous_decision') or '无'}。",
                f"当前对象：`{p['node_id']}`；类型 `{p['type']}`；版本 {m['new_version']}；pipeline `{d['pipeline_version']}`。",
                f"源 SHA-256：`{d['source_hash']}`；当前 evidence fingerprint：`{m['current_evidence_fingerprint']}`。",
                f"原始 PDF：[第 {p['page']} 页]({Path(d['original_pdf_path']).as_posix()})；bbox `{p['bbox']}`。",
                "",
                "当前原文：",
                "",
                "```text",
                p["text"],
                "```",
            ]
        )
        if event:
            packet.extend(
                [
                    "",
                    "历史原文：",
                    "",
                    "```text",
                    event["original_prediction"]["text"],
                    "```",
                ]
            )
        packet.extend(
            [
                "",
                "源 anchors："
                + ", ".join(a["id"] for a in m["current_source_snapshots"]),
                "",
            ]
        )

    pa, pb = papers["A"]["prediction_mapping"], papers["B"]["prediction_mapping"]
    card(
        "A1：关系分析类型",
        "A",
        next(p for p in pa if p["type"] == "RELATIONSHIP_ANALYSIS"),
        "原文不变；METHOD → RELATIONSHIP_ANALYSIS。旧 REVISE 要求‘关系分析’，未对新的 enum 对象作 ACCEPT。请决定该句作为 SEMANTIC/AUTHOR_CLAIM 的关系探索归属是否合适；它不陈述具体关系结果。",
    )
    card(
        "A2a：二维材料工艺片段汇总",
        "A",
        next(p for p in pa if p["type"] == "PROCESS"),
        "这是新的 AI_INTERPRETATION PROCESS：只汇集原文中的剥离、干法转移、拾取/转移、残留聚合物去除、氧化和电接触制备；排除了光谱等表征正文，补回跨块的 PC stamp 句尾。它不是推导工艺、完整执行配方或器件结构综合稿。请对该分组和证据范围作决定。历史 human-source-A-a-fabrication-2 的 ACCEPT 对象是六源的 REVISED_METHOD_VIEW，不能扩展成对这个生产对象的 ACCEPT。",
    )
    oxidation = next(
        p
        for p in pa
        if p.get("previous_decision_id") == "human-source-A-a-fabrication-1"
    )
    card(
        "A2b：同卡的旧氧化子步骤",
        "A",
        oxidation,
        "原氧化 METHOD 原文没变，旧生产决定仍为 REVISE（当时要求完整器件结构/制备覆盖）。当前引用它作为一个材料处理子步骤，完整结构综合稿仍是历史已接受视图。请明确对子步骤归属作决定；不要把 A2a 的 PROCESS 当成覆盖全部结构的那个综合稿。SiN 工艺编译和 DEVICE/图1结构候选可在 paper-a.json 的 graph_node_mapping 找到，属于同一源但不扩展冻结窗口。",
    )
    card(
        "A3：拾取与转移 METHOD",
        "A",
        next(p for p in pa if "Speciﬁcally" in p["text"] and p["type"] == "METHOD"),
        "新生产对象；原文明确 120 °C 拾取、200 °C 转移。已接受扩展视图包含这些事实，但不是对这个独立 METHOD 的类型/当前定位判定，故不自动继承。请决定该原文步骤作为 METHOD 是否合适。",
    )
    card(
        "A4：聚合物去除 METHOD",
        "A",
        next(p for p in pa if p["text"].startswith("After transfer")),
        "新生产对象；原文明确氯仿浸泡 12 h 去除残余 PC。保留 poly- / mer 跨行原文，没有补实验条件。旧扩展视图的 ACCEPT 不自动作用于此独立对象。请决定该原文步骤作为 METHOD 是否合适。",
    )
    card(
        "B1：第三位 1 的上划线修订",
        "B",
        next(
            p
            for p in pb
            if p.get("previous_decision_id") == "human-source-B-b-contact-method-1"
        ),
        "原 raw text (0112) 保留；独立 PDF notation 视图显示 (01 1̅ 2)，ASCII Sb(0 1 -1 2)。原图及浏览器确认上划线在第三个数字 1，末位 2 没有上划线。旧决定是 REVISE 而非修订结果的 ACCEPT。请仅确认这项显示/源忠实度修订。",
    )
    card(
        "B2：on/th 下标修订",
        "B",
        next(
            p
            for p in pb
            if p.get("previous_decision_id") == "human-source-B-b-stability-1"
        ),
        "原 raw text Ion/Vth 保留；独立视图显示 I_on、V_th，24 h、SS 与无明显衰退的限定不变。I_on 是用户明确要求，V_th 曾为模型检查；两者本次再次核对原图。旧 REVISE 没有接受当前显示修订，请仅确认该修订。",
    )
    packet.extend(
        [
            "原图参考：",
            "",
            f"![B 原文上划线]({(root / '.runtime/gate-a-corrections-20261011/paper-b-block-1.png').as_posix()})",
            "",
            f"![B 原文下标]({(root / '.runtime/gate-a-corrections-20261011/paper-b-block-5.png').as_posix()})",
            "",
            "这些是原 PDF 的本地渲染，非生成科学图片。Equation 1 没有新的公式决定请求：原定位映射归 E0，未支持的数学重构继续 unknown。",
        ]
    )
    (report / "TARGETED-REVIEW.md").write_text(
        "\n".join(packet) + "\n", encoding="utf-8"
    )
    overview = """# Gate A reconciliation — 2026-10-11

Current: reviewed Gate A A FAIL / B FAIL; targeted current decisions PENDING; Gate B NOT_STARTED; scientific validity NOT_ASSESSED.

This is a preparatory generic production rerun plus technical reconciliation, not a post-human-review acceptance run. Frozen definitions, thresholds, windows, PDFs, gold and human history are unchanged. No review decision or DB verification record was created.

- [Candidate-level causes and source text](CANDIDATE-DELTA.md)
- [35 equivalent window predictions: binding proposal](EQUIVALENCE-PROPOSAL.md)
- [Six targeted review cards / seven current objects](TARGETED-REVIEW.md)
- [Full A node/edge/quantity/anomaly mapping](paper-a.json)
- [Full B node/edge/quantity/anomaly mapping](paper-b.json)
- [Hashes and immutable history](manifest.json)

Frozen model comparisons remain A precision 16/21 (76.19%), recall 16/17 (94.12%); B precision 17/18 (94.44%), recall 16/16. Matching type/anchor/page, captions, selected quantities and all-node/all-edge provenance remain 100%; A equation N/A, B localization 1/1. These model-key results are distinct from current human acceptance. Identity mismatches are not scientific false positives. A's rejected background target remains a frozen miss.

The v5 generic process compilation excludes nonprocedural characterization text and preserves literal cross-block continuations. Current isolated A has 56 nodes/55 edges, B 76/75; all scientific nodes remain CANDIDATE and no semantic dependency edges were created. Old canonical graphs remain unchanged. Repeated headers/panels remain source data. Equation 1 layout uncertainty is explicit; no normalized algebra or VERIFIED formula is asserted. Newly extracted objects outside the frozen windows remain unreviewed and do not imply full-document quality.

Validation: 39 backend tests, seven reconciliation guards and eight frontend tests passed; Ruff lint/format, mypy and backend/frontend contract checks passed; real public-PDF and both original-PDF Chromium journeys passed. The earlier new synthetic regression failed because a fixture sentence fell below the documented minimum length; the fixture was corrected and the suite rerun successfully. Intermediate proposal directories are retained; this directory supersedes them.

After scoped binding confirmation and targeted decisions, store only the actual user responses in a separate current-review audit, then rerun the same generic pipeline and frozen measurements plus independent current human source adjudication. Any source/hash/version/fingerprint change invalidates a pending binding. Never mutate historical decisions, silently treat REVISE as ACCEPT, weaken thresholds, or begin Gate B here. No commit/push.
"""
    (report / "README.md").write_text(overview, encoding="utf-8")
    manifest = read(report / "manifest.json")
    manifest["artifacts"] = {
        p.name: digest(p)
        for p in report.iterdir()
        if p.is_file() and p.name != "manifest.json"
    }
    manifest["implementation_sha256"] = {
        str(p.relative_to(root)).replace("\\", "/"): digest(p)
        for p in [
            root / "backend/papergraph/extraction.py",
            root / "backend/papergraph/models.py",
            root / "backend/papergraph/worker.py",
            Path(__file__).resolve(),
            root / "evals/reviews/dual-paper/reconcile_current_review.py",
        ]
    }
    (report / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    build(Path(__file__).resolve().parents[3], args.report.resolve())
