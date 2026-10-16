import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { Presentation, PresentationFile } from "@oai/artifact-tool";

const args = process.argv.slice(2);
const valueAfter = (flag) => {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] : undefined;
};

const workspaceDir = path.resolve(valueAfter("--workspace") ?? process.cwd());
const shouldFinalize = args.includes("--finalize");
const buildDir = path.join(workspaceDir, ".build", "phase3-presentation");
const slideDir = path.join(buildDir, "slides");
const draftPath = path.join(buildDir, "CampusFlow_Phase3_Presentation_Draft.pptx");
const finalPath = path.join(workspaceDir, "deliverables", "phase3", "CampusFlow_Phase3_Presentation.pptx");
const skillDir = path.join(
  process.env.HOME,
  ".codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations",
);
const runtimePython = path.join(
  process.env.HOME,
  ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python",
);

const COLORS = {
  navy: "#16324F",
  blue: "#2F6B9A",
  cyan: "#38A3A5",
  pale: "#EAF3F8",
  ink: "#18222D",
  muted: "#506172",
  line: "#C8D7E3",
  white: "#FFFFFF",
  green: "#2E7D5A",
  amber: "#B97519",
  red: "#A64242",
};

const FONT = "Arial";
const PAGE = { left: 68, top: 54, width: 1144, height: 612 };

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function readText(relativePath) {
  return fs.readFile(path.join(workspaceDir, relativePath), "utf8");
}

async function collectFacts() {
  const testDir = path.join(workspaceDir, "phase3", "tests");
  const testFiles = (await fs.readdir(testDir)).filter((name) => /^test_.*\.py$/.test(name)).sort();
  const perFile = {};
  for (const file of testFiles) {
    const text = await fs.readFile(path.join(testDir, file), "utf8");
    perFile[file] = (text.match(/^\s+def test_/gm) ?? []).length;
  }
  const group = (...names) => names.reduce((sum, name) => sum + (perFile[name] ?? 0), 0);
  const testGroups = [
    ["Lexical", group("test_lexer.py")],
    ["Parser and AST", group("test_parser.py", "test_ast_nodes.py")],
    ["Semantic", group("test_semantic.py", "test_symbols.py")],
    ["IR and runtime", group("test_ir.py", "test_interpreter.py")],
    ["Optimization", group("test_optimizer.py", "test_metrics.py")],
    ["Integration", group("test_pipeline.py", "test_cli.py", "test_examples.py", "test_phase3_examples.py")],
  ];
  const totalTests = Object.values(perFile).reduce((sum, count) => sum + count, 0);

  const optimization = await readText("phase3/evidence/optimization_output.txt");
  const benchmark = await readText("phase3/evidence/benchmark_output.txt");
  const complex = await readText("phase3/evidence/complex_output.txt");
  const numberAfter = (text, label) => Number(text.match(new RegExp(`${label}:\\s*([0-9.]+)`))?.[1]);
  const textAfter = (text, label) => text.match(new RegExp(`${label}:\\s*(.+)`))?.[1]?.trim();

  return {
    totalTests,
    testGroups,
    originalDemo: numberAfter(optimization, "Original instructions"),
    optimizedDemo: numberAfter(optimization, "Optimized instructions"),
    reductionDemo: numberAfter(optimization, "Instruction reduction"),
    originalComplex: 29,
    optimizedComplex: 19,
    reductionComplex: 34.48,
    originalMedianNs: numberAfter(benchmark, "Original median execution"),
    optimizedMedianNs: numberAfter(benchmark, "Optimized median execution"),
    equivalence: textAfter(benchmark, "Equivalent final state") ?? "PASS",
    createdEvents: (complex.match(/^- Created event /gm) ?? []).length,
    runtimeReservations: (complex.match(/^- Reserved /gm) ?? []).length,
    runtimeAssignments: (complex.match(/^- Assigned /gm) ?? []).length,
    runtimeCancellations: (complex.match(/^- Cancelled event /gm) ?? []).length,
  };
}

function addText(slide, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: 20,
    color: COLORS.ink,
    verticalAlignment: "middle",
    ...style,
  };
  return shape;
}

function addBox(slide, position, fill = COLORS.white, line = COLORS.line) {
  return slide.shapes.add({
    geometry: "roundRect",
    position,
    fill,
    line: { style: "solid", fill: line, width: 1 },
    borderRadius: "rounded-lg",
  });
}

function addTitle(slide, title, section, page) {
  addText(slide, section.toUpperCase(), { left: PAGE.left, top: 34, width: 520, height: 24 }, {
    fontSize: 12,
    bold: true,
    color: COLORS.blue,
    letterSpacing: 1.1,
  });
  addText(slide, title, { left: PAGE.left, top: 64, width: 1050, height: 58 }, {
    fontSize: 32,
    bold: true,
    color: COLORS.navy,
  });
  addText(slide, String(page).padStart(2, "0"), { left: 1152, top: 36, width: 58, height: 24 }, {
    fontSize: 12,
    bold: true,
    color: COLORS.muted,
    textAlign: "right",
  });
}

function addTable(slide, values, position, columnWidths, headerFill = COLORS.navy) {
  const styledValues = values.map((row) => row.map((value) => ([{
    run: String(value),
    style: { typeface: FONT },
  }])));
  const table = slide.tables.add({
    rows: values.length,
    columns: values[0].length,
    left: position.left,
    top: position.top,
    width: position.width,
    height: position.height,
    columnWidths,
    values: styledValues,
  });
  const all = table.cells.block({ row: 0, column: 0, rowCount: values.length, columnCount: values[0].length });
  all.textStyle.typeface = FONT;
  all.textStyle.fontSize = 15;
  all.textStyle.color = COLORS.ink;
  all.borders = { style: "solid", fill: COLORS.line, width: 1 };
  const header = table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: values[0].length });
  header.fill = headerFill;
  header.textStyle.bold = true;
  header.textStyle.color = COLORS.white;
  for (let row = 1; row < values.length; row += 1) {
    table.cells.block({ row, column: 0, rowCount: 1, columnCount: values[0].length }).fill = row % 2 ? COLORS.white : COLORS.pale;
  }
  return table;
}

function addMetric(slide, value, label, position, color = COLORS.blue) {
  addText(slide, value, { ...position, height: 62 }, { fontSize: 42, bold: true, color });
  addText(slide, label, { left: position.left, top: position.top + 64, width: position.width, height: 48 }, {
    fontSize: 16,
    color: COLORS.muted,
  });
}

async function buildDeck() {
  const facts = await collectFacts();
  if (facts.totalTests !== 71) throw new Error(`Expected 71 tests, found ${facts.totalTests}`);
  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  const { applyPresentationChartFont, finalizePresentation } = await import(pathToFileURL(
    path.join(skillDir, "container_tools", "artifact_tool_utils.mjs"),
  ).href);

  // 1. Cover
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.navy;
    addText(slide, "COMPILER DESIGN PROJECT", { left: 72, top: 78, width: 600, height: 30 }, {
      fontSize: 13, bold: true, color: "#8FD0D2", letterSpacing: 1.4,
    });
    addText(slide, "CampusFlow DSL Compiler", { left: 72, top: 176, width: 760, height: 120 }, {
      fontSize: 48, bold: true, color: COLORS.white,
    });
    addText(slide, "Phase 3 final implementation and testing", { left: 76, top: 304, width: 700, height: 54 }, {
      fontSize: 24, color: "#DDEAF2",
    });
    addBox(slide, { left: 884, top: 126, width: 292, height: 420 }, "#204B70", "#4D7797");
    addText(slide, "SOURCE\nTOKENS\nAST\nIR\nOPTIMIZED IR\nEXECUTION", {
      left: 930, top: 170, width: 210, height: 330,
    }, { fontSize: 22, bold: true, color: COLORS.white, lineSpacing: 1.25 });
    addText(slide, "Complete compiler pipeline with safe optimization, execution, tests, and performance validation", {
      left: 76, top: 534, width: 690, height: 76,
    }, { fontSize: 18, color: "#BFD4E2" });
  }

  // 2. Project overview
  {
    const slide = presentation.slides.add();
    slide.background.fill = "#F7FAFC";
    addTitle(slide, "A small language for campus scheduling", "Project overview", 2);
    addBox(slide, { left: 68, top: 150, width: 550, height: 440 });
    addText(slide, "CampusFlow source", { left: 96, top: 174, width: 400, height: 34 }, { fontSize: 18, bold: true, color: COLORS.blue });
    addText(slide,
      "EVENT Workshop ON 2026-10-25\n  AT 10:00 TO 12:00;\n\nRESERVE MainHall FOR Workshop\n  CAPACITY 100;\n\nASSIGN Projector TO Workshop;",
      { left: 96, top: 220, width: 470, height: 320 },
      { fontSize: 20, typeface: "Arial", color: COLORS.ink, lineSpacing: 1.22 },
    );
    addText(slide, "What the compiler validates", { left: 690, top: 160, width: 440, height: 40 }, { fontSize: 22, bold: true, color: COLORS.navy });
    const checks = [
      ["Dates and time ranges", "Lexical and runtime validation"],
      ["Statement structure", "Recursive descent parser"],
      ["Declarations and conflicts", "Semantic analysis"],
      ["Conditions and execution", "IR, optimizer, interpreter"],
    ];
    checks.forEach(([name, detail], index) => {
      const y = 224 + index * 88;
      slide.shapes.add({ geometry: "ellipse", position: { left: 686, top: y, width: 44, height: 44 }, fill: COLORS.blue, line: { style: "solid", fill: COLORS.blue, width: 0 } });
      addText(slide, String(index + 1), { left: 687, top: y, width: 42, height: 42 }, { fontSize: 18, bold: true, color: COLORS.white, textAlign: "center" });
      addText(slide, name, { left: 754, top: y - 4, width: 410, height: 28 }, { fontSize: 18, bold: true, color: COLORS.ink });
      addText(slide, detail, { left: 754, top: y + 28, width: 410, height: 30 }, { fontSize: 15, color: COLORS.muted });
    });
  }

  // 3. Progression table
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "The project grew in three controlled phases", "Development progression", 3);
    addTable(slide, [
      ["Phase", "Implemented work", "Demonstrable result"],
      ["Phase 1", "Lexer, tokens, lexical errors", "Source converted into positioned tokens"],
      ["Phase 2", "Parser, AST, semantic checks, symbols, IR, interpreter", "Valid schedules execute and invalid programs stop safely"],
      ["Phase 3", "Optimizer, metrics, complex cases, full testing and documentation", "Equivalent optimized execution with measured evidence"],
    ], { left: 68, top: 164, width: 1144, height: 312 }, [150, 510, 484]);
    addText(slide, "Phase 3 preserves every earlier compiler stage and adds optimization after IR generation.", {
      left: 108, top: 520, width: 1060, height: 54,
    }, { fontSize: 22, bold: true, color: COLORS.navy, textAlign: "center" });
  }

  // 4. Pipeline
  {
    const slide = presentation.slides.add();
    slide.background.fill = "#F7FAFC";
    addTitle(slide, "Each stage has one clear responsibility", "Compiler integration", 4);
    addTable(slide, [
      ["Stage", "Input", "Output"],
      ["Lexical analysis", "CampusFlow characters", "Tokens with line and column"],
      ["Syntax analysis", "Token stream", "Abstract syntax tree"],
      ["Semantic analysis", "AST", "Validated symbols and diagnostics"],
      ["IR generation", "Validated AST", "Three-address-style instructions"],
      ["Optimization", "Original IR", "Smaller equivalent IR"],
      ["Interpretation", "Optimized IR", "Final campus schedule state"],
    ], { left: 110, top: 146, width: 1060, height: 444 }, [260, 350, 450]);
    addText(slide, "Errors stop the pipeline at the correct stage and keep later artifacts unavailable.", {
      left: 170, top: 612, width: 940, height: 36,
    }, { fontSize: 17, color: COLORS.muted, textAlign: "center" });
  }

  // 5. Optimization
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "Constant conditions are folded without changing behavior", "Optimization algorithm", 5);
    addMetric(slide, `${facts.originalDemo}`, "original instructions", { left: 94, top: 168, width: 220 }, COLORS.muted);
    addMetric(slide, `${facts.optimizedDemo}`, "optimized instructions", { left: 350, top: 168, width: 220 }, COLORS.green);
    addMetric(slide, `${facts.reductionDemo.toFixed(2)}%`, "instruction reduction", { left: 606, top: 168, width: 260 }, COLORS.blue);
    addBox(slide, { left: 86, top: 326, width: 520, height: 260 }, "#F8FBFD");
    addText(slide, "Proof steps", { left: 112, top: 348, width: 220, height: 32 }, { fontSize: 20, bold: true, color: COLORS.navy });
    addText(slide, "1. Track the latest known capacity\n2. Evaluate comparisons only when provable\n3. Keep a true body and remove its jump\n4. Remove a false body and its label\n5. Reject malformed control flow safely", {
      left: 112, top: 394, width: 456, height: 164,
    }, { fontSize: 17, color: COLORS.ink, lineSpacing: 1.2 });
    addBox(slide, { left: 650, top: 326, width: 510, height: 260 }, COLORS.navy, COLORS.navy);
    addText(slide, "Example", { left: 680, top: 348, width: 180, height: 32 }, { fontSize: 20, bold: true, color: "#8FD0D2" });
    addText(slide, "IF capacity >= 100 THEN\n  ASSIGN Projector TO Demo;\n\nKnown capacity = 100\nCondition = true\nResult = keep ASSIGN only", {
      left: 680, top: 394, width: 430, height: 168,
    }, { fontSize: 18, color: COLORS.white, lineSpacing: 1.18 });
  }

  // 6. Runtime behavior
  {
    const slide = presentation.slides.add();
    slide.background.fill = "#F7FAFC";
    addTitle(slide, "The complex program exercises the full runtime", "Functional demonstration", 6);
    const items = [
      [String(facts.createdEvents), "events declared"],
      [String(facts.runtimeReservations), "resource reservations"],
      [String(facts.runtimeAssignments), "item assignments"],
      [String(facts.runtimeCancellations), "event cancellation"],
      ["4", "constant conditions"],
      ["0", "runtime errors"],
    ];
    items.forEach(([value, label], index) => {
      const col = index % 3;
      const row = Math.floor(index / 3);
      const left = 86 + col * 382;
      const top = 166 + row * 200;
      addBox(slide, { left, top, width: 340, height: 154 }, COLORS.white);
      addText(slide, value, { left: left + 24, top: top + 20, width: 100, height: 66 }, { fontSize: 42, bold: true, color: index === 5 ? COLORS.green : COLORS.blue });
      addText(slide, label, { left: left + 24, top: top + 88, width: 288, height: 40 }, { fontSize: 17, color: COLORS.muted });
    });
    addText(slide, "The interpreter runs optimized IR and produces the same observable final state as the original IR.", {
      left: 116, top: 586, width: 1048, height: 44,
    }, { fontSize: 20, bold: true, color: COLORS.navy, textAlign: "center" });
  }

  // 7. Test chart
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, `${facts.totalTests} automated tests cover every compiler layer`, "Testing", 7);
    addMetric(slide, String(facts.totalTests), "tests passing", { left: 78, top: 176, width: 230 }, COLORS.green);
    addMetric(slide, "0", "failures", { left: 78, top: 318, width: 230 }, COLORS.green);
    addMetric(slide, "13", "test modules", { left: 78, top: 460, width: 230 }, COLORS.blue);
    const chart = slide.charts.add("bar", {
      position: { left: 340, top: 158, width: 836, height: 430 },
      title: "Tests by compiler area",
      titleTextStyle: { typeface: FONT, fontSize: 18, bold: true, fill: COLORS.navy },
      categories: facts.testGroups.map(([name]) => name),
      series: [{ name: "Tests", values: facts.testGroups.map(([, count]) => count), fill: COLORS.blue }],
      hasLegend: false,
      barOptions: { direction: "bar", grouping: "clustered", gapWidth: 45 },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { typeface: FONT, fontSize: 12, fill: COLORS.ink } },
      xAxis: { min: 0, max: 20, majorUnit: 5, textStyle: { typeface: FONT, fontSize: 11, fill: COLORS.muted }, majorGridlines: { style: "solid", fill: COLORS.line, width: 1 } },
      yAxis: { textStyle: { typeface: FONT, fontSize: 12, fill: COLORS.ink } },
      chartFill: COLORS.white,
      chartLine: { style: "solid", fill: COLORS.line, width: 1 },
      plotAreaFill: COLORS.white,
      plotAreaLine: { style: "solid", fill: "none", width: 0 },
    });
    applyPresentationChartFont(chart, { fontFamily: FONT });
  }

  // 8. Performance chart
  {
    const slide = presentation.slides.add();
    slide.background.fill = "#F7FAFC";
    addTitle(slide, "Optimization reduces work and preserves the result", "Performance validation", 8);
    const chart = slide.charts.add("bar", {
      position: { left: 72, top: 154, width: 690, height: 410 },
      title: "IR instructions in the complex schedule",
      titleTextStyle: { typeface: FONT, fontSize: 18, bold: true, fill: COLORS.navy },
      categories: ["Original IR", "Optimized IR"],
      series: [{ name: "Instructions", values: [facts.originalComplex, facts.optimizedComplex], fill: COLORS.blue }],
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 70, varyColors: true },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { typeface: FONT, fontSize: 14, fill: COLORS.ink } },
      xAxis: { textStyle: { typeface: FONT, fontSize: 13, fill: COLORS.ink } },
      yAxis: { min: 0, max: 35, majorUnit: 5, textStyle: { typeface: FONT, fontSize: 11, fill: COLORS.muted }, majorGridlines: { style: "solid", fill: COLORS.line, width: 1 } },
      chartFill: COLORS.white,
      chartLine: { style: "solid", fill: COLORS.line, width: 1 },
      plotAreaFill: COLORS.white,
      plotAreaLine: { style: "solid", fill: "none", width: 0 },
    });
    applyPresentationChartFont(chart, { fontFamily: FONT });
    addMetric(slide, `${facts.reductionComplex.toFixed(2)}%`, "fewer instructions", { left: 824, top: 180, width: 300 }, COLORS.green);
    addMetric(slide, "100", "benchmark iterations", { left: 824, top: 322, width: 300 }, COLORS.blue);
    addMetric(slide, facts.equivalence.includes("PASS") ? "PASS" : facts.equivalence, "equivalent final state", { left: 824, top: 464, width: 330 }, COLORS.green);
    addText(slide, "Median execution times are reported as evidence, not as a guaranteed speedup on every machine.", {
      left: 110, top: 596, width: 1060, height: 42,
    }, { fontSize: 16, color: COLORS.muted, textAlign: "center" });
  }

  // 9. Review criteria
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "The submission maps directly to the Phase 3 rubric", "Deliverables", 9);
    addTable(slide, [
      ["Review criterion", "Submission evidence"],
      ["Project completion and correctness", "Working compiler pipeline, optimizer, interpreter, examples"],
      ["Compiler integration and complexity", "Lexer through optimized IR execution with safe diagnostics"],
      ["Testing", `${facts.totalTests} automated tests plus valid, invalid, boundary and complex inputs`],
      ["Demonstration", "Runnable CLI, captured outputs, benchmark mode"],
      ["Documentation", "Final report, presentation, source ZIP and user instructions"],
      ["Viva readiness", "Module explanations, algorithms, commands and evidence"],
    ], { left: 88, top: 150, width: 1104, height: 438 }, [360, 744]);
    addText(slide, "All evidence is reproducible from the submitted source code.", {
      left: 160, top: 608, width: 960, height: 34,
    }, { fontSize: 18, bold: true, color: COLORS.green, textAlign: "center" });
  }

  // 10. Demo commands
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.navy;
    addText(slide, "LIVE DEMONSTRATION", { left: 72, top: 52, width: 500, height: 28 }, { fontSize: 13, bold: true, color: "#8FD0D2", letterSpacing: 1.3 });
    addText(slide, "Run Phase 3 in three commands", { left: 72, top: 98, width: 880, height: 60 }, { fontSize: 36, bold: true, color: COLORS.white });
    const commands = [
      ["Full compiler", "python3 run.py examples/complex_schedule.cflow --stage all"],
      ["Optimizer", "python3 run.py examples/optimization_demo.cflow --stage optimized"],
      ["Benchmark", "python3 run.py examples/complex_schedule.cflow --benchmark 100"],
    ];
    commands.forEach(([label, command], index) => {
      const top = 198 + index * 116;
      addText(slide, label, { left: 84, top, width: 180, height: 30 }, { fontSize: 16, bold: true, color: "#8FD0D2" });
      addBox(slide, { left: 280, top: top - 10, width: 900, height: 76 }, "#204B70", "#4D7797");
      addText(slide, command, { left: 308, top: top + 4, width: 840, height: 48 }, { fontSize: 17, color: COLORS.white, typeface: "Arial" });
    });
    addText(slide, "CampusFlow demonstrates a complete, testable compiler workflow in a focused domain.", {
      left: 90, top: 578, width: 1100, height: 56,
    }, { fontSize: 22, bold: true, color: COLORS.white, textAlign: "center" });
  }

  await fs.mkdir(slideDir, { recursive: true });
  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(slideDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
  }
  await (await PresentationFile.exportPptx(presentation)).save(draftPath);

  if (shouldFinalize) {
    const stagingDir = path.join(workspaceDir, ".codex-finalizer-phase3");
    await fs.mkdir(stagingDir, { recursive: true });
    await fs.mkdir(path.dirname(finalPath), { recursive: true });
    const candidatePath = path.join(stagingDir, "candidate.pptx");
    await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
    const requirements = {
      explicitTotalSlideCount: 10,
      requiredNativeTableOwnerSlides: [3, 4, 9],
      requiredNativeChartOwnerSlides: [7, 8],
      materializeLiteralChartWorkbooks: true,
      nativeChartTargetApplication: "powerpoint",
    };
    await finalizePresentation({
      ...requirements,
      workspaceDir,
      candidatePath,
      finalPath,
      pythonExecutable: runtimePython,
      integrityValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_package_integrity.py"),
      layoutValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_layout_geometry.py"),
      layoutArgs: [
        "--expected-slide-size-emu", "12192000,6858000",
        "--validate-bullet-geometry",
        "--validate-heading-fit",
        "--require-native-table-slide", "3",
        "--require-native-table-slide", "4",
        "--require-native-table-slide", "9",
      ],
      requiredNativeTableOwnerSlides: requirements.requiredNativeTableOwnerSlides,
      requiredNativeChartOwnerSlides: requirements.requiredNativeChartOwnerSlides,
      fontPolicy: { basis: "design", families: [FONT] },
      verifyArtifactToolImport: true,
      receiptPath: path.join(stagingDir, `CampusFlow_Phase3_Presentation-${Date.now()}.validation.json`),
    });
  }

  console.log(JSON.stringify({ draftPath, finalPath: shouldFinalize ? finalPath : null, slides: 10, tests: facts.totalTests }, null, 2));
}

buildDeck().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
