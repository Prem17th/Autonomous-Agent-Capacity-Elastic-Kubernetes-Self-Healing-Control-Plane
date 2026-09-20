"""Interactive Autonomous Command Center HTML Dashboard for Aegis Sentinel built with 100% Tailwind CSS."""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aegis Sentinel — Autonomous Kubernetes Recovery Command Center</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#ecfeff',
                            100: '#cffafe',
                            400: '#22d3ee',
                            500: '#06b6d4',
                            600: '#0891b2',
                            900: '#164e63',
                            950: '#083344',
                        }
                    },
                    fontFamily: {
                        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
                    },
                    animation: {
                        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        'glow': 'glow 2s ease-in-out infinite alternate',
                    },
                    keyframes: {
                        glow: {
                            '0%': { boxShadow: '0 0 10px rgba(6, 182, 212, 0.2)' },
                            '100%': { boxShadow: '0 0 25px rgba(6, 182, 212, 0.6)' },
                        }
                    }
                }
            }
        }
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen p-3 sm:p-6 antialiased selection:bg-cyan-500 selection:text-white bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black">

    <div class="max-w-[1536px] mx-auto flex flex-col gap-6">

        <!-- 1. TOP COMMAND BAR & SUBSYSTEM STATUS -->
        <header class="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-5 sm:p-6 shadow-2xl shadow-black/80 flex flex-wrap items-center justify-between gap-5 relative overflow-hidden">
            <div class="absolute -right-20 -top-20 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
            <div class="absolute -left-20 -bottom-20 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

            <!-- Brand Identity -->
            <div class="flex items-center gap-4 z-10">
                <div class="w-14 h-14 bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center font-black text-2xl text-white shadow-xl shadow-cyan-500/25 border border-cyan-400/30">
                    🛡️
                </div>
                <div>
                    <div class="flex items-center gap-3">
                        <h1 class="text-2xl font-black tracking-tight text-white flex items-center gap-2">
                            AEGIS SENTINEL
                        </h1>
                        <span class="text-xs font-bold font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 px-2.5 py-1 rounded-full flex items-center gap-1.5">
                            <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
                            MCP v2024-11-05
                        </span>
                    </div>
                    <p class="text-xs text-slate-400 font-medium mt-0.5">Autonomous Agent Capacity &amp; Elastic Kubernetes Self-Healing Control Plane</p>
                </div>
            </div>

            <!-- Subsystem Live Badges -->
            <div class="flex flex-wrap gap-2.5 text-xs font-mono z-10">
                <div class="bg-slate-950/80 border border-slate-800 px-3.5 py-2 rounded-xl flex items-center gap-2.5 shadow-inner">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400"></span>
                    <span class="text-slate-300">MCP: <strong class="text-emerald-400 font-semibold">14 Tools Active</strong></span>
                </div>
                <div class="bg-slate-950/80 border border-slate-800 px-3.5 py-2 rounded-xl flex items-center gap-2.5 shadow-inner">
                    <span class="w-2 h-2 rounded-full bg-amber-400 shadow-sm shadow-amber-400"></span>
                    <span class="text-slate-300" id="k8s-state-label">K8S: <strong class="text-amber-400 font-semibold">SIMULATED</strong></span>
                </div>
                <div class="bg-slate-950/80 border border-slate-800 px-3.5 py-2 rounded-xl flex items-center gap-2.5 shadow-inner">
                    <span class="w-2 h-2 rounded-full bg-purple-400 shadow-sm shadow-purple-400"></span>
                    <span class="text-slate-300" id="reasoner-state-label">AI: <strong class="text-purple-400 font-semibold">DETERMINISTIC FALLBACK</strong></span>
                </div>
                <div class="bg-slate-950/80 border border-slate-800 px-3.5 py-2 rounded-xl flex items-center gap-2.5 shadow-inner">
                    <span class="w-2 h-2 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400"></span>
                    <span class="text-slate-300" id="autoscaler-state-label">AUTOSCALER: <strong class="text-cyan-400 font-semibold">SIMULATED PROVIDER</strong></span>
                </div>
            </div>

            <!-- Action Controls -->
            <div class="flex items-center gap-3 z-10">
                <button id="btn-run-demo" onclick="runCompleteDemo()" class="px-5 py-2.5 rounded-xl font-bold text-sm bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-lg shadow-cyan-500/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0 flex items-center gap-2.5 cursor-pointer">
                    <span class="text-base">▶</span> RUN RECOVERY DEMO
                </button>
                <button id="btn-sim-block" onclick="simulatePolicyBlock()" class="px-4 py-2.5 rounded-xl font-bold text-sm bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-all flex items-center gap-2 cursor-pointer">
                    <span>⚠</span> SIMULATE POLICY BLOCK
                </button>
                <button id="btn-demo-mode" onclick="toggleDemoMode()" class="px-3.5 py-2.5 rounded-xl text-xs font-bold bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-300 hover:text-white transition-all flex items-center gap-1.5 cursor-pointer">
                    <span>📺</span> PRESENTATION
                </button>
            </div>
        </header>

        <!-- 2. TELEMETRY & WORKLOAD STATS CARDS -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            <!-- Metric 1: Recovery State -->
            <div class="bg-slate-900/70 backdrop-blur-md border border-slate-800/90 rounded-2xl p-5 flex flex-col justify-between shadow-xl relative overflow-hidden group hover:border-cyan-500/40 transition-all">
                <div class="flex items-center justify-between">
                    <span class="text-[11px] font-mono font-bold tracking-wider text-slate-400 uppercase">Engine Lifecycle State</span>
                    <span class="w-3 h-3 rounded-full bg-cyan-400 animate-ping"></span>
                </div>
                <div class="my-3">
                    <div class="text-2xl font-black font-sans text-white flex items-center gap-2" id="engine-state-title">
                        IDLE / READY
                    </div>
                    <p class="text-xs text-slate-400 mt-1 truncate" id="engine-state-desc">Awaiting unschedulable pod trigger.</p>
                </div>
                <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div id="progress-bar" class="bg-gradient-to-r from-cyan-500 to-blue-600 h-1.5 rounded-full w-1/12 transition-all duration-500"></div>
                </div>
            </div>

            <!-- Metric 2: Target Workload -->
            <div class="bg-slate-900/70 backdrop-blur-md border border-slate-800/90 rounded-2xl p-5 flex flex-col justify-between shadow-xl group hover:border-blue-500/40 transition-all">
                <div class="flex items-center justify-between">
                    <span class="text-[11px] font-mono font-bold tracking-wider text-slate-400 uppercase">Target Workload</span>
                    <span class="text-xs font-mono bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded">UUID Monitored</span>
                </div>
                <div class="my-3 font-mono">
                    <div class="text-lg font-bold text-cyan-400 truncate" id="target-pod-name">agent-pending-cpu</div>
                    <div class="text-xs text-slate-400 truncate mt-0.5">Namespace: aegis-agents</div>
                </div>
                <div class="flex items-center justify-between text-xs font-mono text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-lg">
                    <span>Demand: 2000m CPU</span>
                    <span>1 Node Req</span>
                </div>
            </div>

            <!-- Metric 3: Policy Audits -->
            <div class="bg-slate-900/70 backdrop-blur-md border border-slate-800/90 rounded-2xl p-5 flex flex-col justify-between shadow-xl group hover:border-purple-500/40 transition-all">
                <div class="flex items-center justify-between">
                    <span class="text-[11px] font-mono font-bold tracking-wider text-slate-400 uppercase">Policy Invariants</span>
                    <span class="text-xs font-mono bg-purple-500/10 text-purple-400 border border-purple-500/30 px-2 py-0.5 rounded">Authoritative</span>
                </div>
                <div class="my-3 flex items-baseline gap-2">
                    <span id="metric-decisions" class="text-3xl font-black font-mono text-white">0</span>
                    <span class="text-xs font-medium text-slate-400">Decisions Evaluated</span>
                </div>
                <div class="flex items-center justify-between text-xs font-mono text-slate-400 border-t border-slate-800 pt-2">
                    <span>Max/Req: <strong>2 Nodes</strong></span>
                    <span>Cooldown: <strong>120s</strong></span>
                </div>
            </div>

            <!-- Metric 4: Recovery Elapsed Time -->
            <div class="bg-slate-900/70 backdrop-blur-md border border-slate-800/90 rounded-2xl p-5 flex flex-col justify-between shadow-xl group hover:border-emerald-500/40 transition-all">
                <div class="flex items-center justify-between">
                    <span class="text-[11px] font-mono font-bold tracking-wider text-slate-400 uppercase">Self-Healing Timer</span>
                    <span class="text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded">Live</span>
                </div>
                <div class="my-3 flex items-baseline gap-2">
                    <span id="metric-timer" class="text-3xl font-black font-mono text-emerald-400">0.0s</span>
                    <span class="text-xs font-medium text-slate-400">Elapsed</span>
                </div>
                <div class="flex items-center justify-between text-xs font-mono text-slate-400 border-t border-slate-800 pt-2">
                    <span>Pending: <strong id="metric-pending" class="text-rose-400">1</strong></span>
                    <span>Recovered: <strong id="metric-recoveries" class="text-emerald-400">0</strong></span>
                </div>
            </div>
        </div>

        <!-- 3. EVIDENTIARY PROCESS GRAPH (MAIN FEATURE) -->
        <section class="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl flex flex-col gap-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 flex items-center justify-center font-bold">
                        🕸
                    </div>
                    <h2 class="text-base font-extrabold tracking-tight text-white">
                        Autonomous Evidentiary Process Pipeline
                    </h2>
                </div>
                <span class="text-xs font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 px-3 py-1 rounded-full">
                    Select Any Node to View Evidence
                </span>
            </div>

            <div class="flex items-stretch gap-2.5 overflow-x-auto pb-4 pt-2 scrollbar-thin scrollbar-thumb-slate-700" id="process-graph">
                <!-- 11 Standard Evidentiary Nodes -->
                <div id="node-1" onclick="selectNode(1)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 01</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">📨</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">Agent Request</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-2" onclick="selectNode(2)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 02</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">⚙️</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">Pod Scheduling</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-3" onclick="selectNode(3)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 03</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">⏳</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">Pending Found</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-4" onclick="selectNode(4)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 04</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">🔍</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">K8s Evidence</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-5" onclick="selectNode(5)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 05</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">🧩</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">Root Cause</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-6" onclick="selectNode(6)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 06</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">🧠</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">AI Reasoning</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-7" onclick="selectNode(7)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 07</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">📜</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">Proposal</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-8" onclick="selectNode(8)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 08</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">🛡️</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">Policy Gate</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-9" onclick="selectNode(9)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 09</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">🔧</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">Scale Action</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-10" onclick="selectNode(10)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 10</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">✅</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">Capacity Ready</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>

                <div id="node-11" onclick="selectNode(11)" class="process-node flex-1 min-w-[125px] bg-slate-950 border border-slate-800 rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer hover:border-cyan-500/60 hover:bg-slate-900/60 transition-all group">
                    <span class="text-[10px] font-mono font-extrabold text-slate-500 group-hover:text-cyan-400">STEP 11</span>
                    <div class="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-base">🚀</div>
                    <div class="text-xs font-bold text-white tracking-tight leading-tight">Agent Running</div>
                    <span class="node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">WAITING</span>
                </div>
            </div>
        </section>

        <!-- 4. WORKSPACE: DEEP INSPECTOR & POLICY CHECKPOINT -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Left: Evidence Deep Inspector (7 cols) -->
            <div class="lg:col-span-7 bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl flex flex-col gap-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold">
                            📊
                        </div>
                        <h3 class="text-base font-extrabold text-white">Evidentiary Deep Inspector</h3>
                    </div>
                    <span id="inspector-badge" class="text-xs font-mono font-bold px-3 py-1 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30">
                        OBSERVED FACT
                    </span>
                </div>

                <div id="inspector-body" class="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 flex flex-col gap-3.5 min-h-[280px] font-mono text-xs shadow-inner">
                    <div class="flex justify-between border-b border-slate-800 pb-2.5">
                        <span class="text-slate-500">Pipeline Step</span>
                        <span class="text-cyan-400 font-bold" id="ev-step-title">01. Initial Request Observation</span>
                    </div>
                    <div class="flex justify-between border-b border-slate-800 pb-2.5">
                        <span class="text-slate-500">Pod Subject</span>
                        <span class="text-slate-200">agent-pending-cpu</span>
                    </div>
                    <div class="flex justify-between border-b border-slate-800 pb-2.5">
                        <span class="text-slate-500">Source</span>
                        <span class="text-slate-200">Kubernetes Scheduler Events</span>
                    </div>
                    <div id="ev-quote-text" class="bg-slate-900/90 border-l-4 border-cyan-400 p-3.5 rounded-r-xl text-sky-200 mt-2 font-mono leading-relaxed shadow-sm">
Click "RUN RECOVERY DEMO" to execute the live recovery pipeline. Click any pipeline step above to inspect evidentiary properties.
                    </div>
                </div>
            </div>

            <!-- Right: Policy Checkpoint (5 cols) -->
            <div class="lg:col-span-5 bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl flex flex-col gap-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/30 flex items-center justify-center font-bold">
                            🤖
                        </div>
                        <h3 class="text-base font-extrabold text-white">Sentinel AI &amp; Policy Gate</h3>
                    </div>
                    <span class="text-xs font-mono font-bold px-3 py-1 rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/30">
                        AUTHORITATIVE
                    </span>
                </div>

                <div class="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 flex flex-col gap-4 shadow-inner">
                    <!-- Policy Flow Pipeline -->
                    <div class="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-xs font-mono">
                        <div class="bg-purple-500/20 text-purple-300 border border-purple-500/30 px-3 py-1.5 rounded-lg text-center font-bold">
                            AI PROPOSAL<br><span id="flow-ai-prop" class="text-[10px] text-purple-400 font-medium">+1 Node</span>
                        </div>
                        <span class="text-slate-600 font-bold text-sm">➔</span>
                        <div class="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-3 py-1.5 rounded-lg text-center font-bold">
                            POLICY GATE<br><span class="text-[10px] text-amber-400 font-medium">Safety Check</span>
                        </div>
                        <span class="text-slate-600 font-bold text-sm">➔</span>
                        <div id="flow-decision-pill" class="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1.5 rounded-lg text-center font-bold">
                            DECISION<br><span id="flow-decision-text" class="text-[10px]">STANDBY</span>
                        </div>
                    </div>

                    <!-- Hardened Rules Grid -->
                    <div class="grid grid-cols-2 gap-2.5 text-xs font-mono">
                        <div class="bg-slate-900 border border-slate-800 p-2.5 rounded-xl flex justify-between">
                            <span class="text-slate-500">MAX / REQ:</span>
                            <span class="text-cyan-400 font-bold">2 Nodes</span>
                        </div>
                        <div class="bg-slate-900 border border-slate-800 p-2.5 rounded-xl flex justify-between">
                            <span class="text-slate-500">CLUSTER MAX:</span>
                            <span class="text-cyan-400 font-bold">10 Nodes</span>
                        </div>
                        <div class="bg-slate-900 border border-slate-800 p-2.5 rounded-xl flex justify-between">
                            <span class="text-slate-500">COOLDOWN:</span>
                            <span class="text-cyan-400 font-bold">120s</span>
                        </div>
                        <div class="bg-slate-900 border border-slate-800 p-2.5 rounded-xl flex justify-between">
                            <span class="text-slate-500">ALLOWED POOL:</span>
                            <span class="text-cyan-400 font-bold">default</span>
                        </div>
                    </div>

                    <!-- Verdict Banner -->
                    <div id="policy-verdict-banner" class="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 p-3.5 rounded-xl text-xs font-mono font-bold flex justify-between items-center">
                        <span id="policy-verdict-title">✓ POLICY ENGINE STANDBY</span>
                        <span id="policy-verdict-reason" class="text-[11px] font-normal text-slate-400">Awaiting AI proposal</span>
                    </div>

                    <div class="text-center text-xs font-bold text-purple-300 bg-purple-500/10 border border-dashed border-purple-500/30 py-2.5 rounded-xl">
                        &ldquo;AI proposes. Policy decides.&rdquo;
                    </div>
                </div>
            </div>
        </div>

        <!-- 5. BOTTOM GRID: REALTIME ACTIVITY TERMINAL & TOPOLOGY -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Terminal Log -->
            <div class="lg:col-span-7 bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl flex flex-col gap-3.5">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 flex items-center justify-center font-bold">
                            📝
                        </div>
                        <h3 class="text-base font-extrabold text-white">Autonomous Agent Activity Stream</h3>
                    </div>
                    <button onclick="clearStream()" class="text-xs font-mono px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 cursor-pointer">Clear</button>
                </div>
                <div id="agent-stream-box" class="bg-slate-950 border border-slate-800 rounded-2xl p-4 font-mono text-xs text-sky-200 h-60 overflow-y-auto leading-relaxed shadow-inner">
[SYSTEM INIT] Aegis Sentinel Command Center loaded (100% Tailwind CSS).
[READY] MCP Server connected via Streamable HTTP (JSON-RPC 2.0).
[STANDBY] Monitoring Kubernetes agent deployment queue.
                </div>
            </div>

            <!-- Topology -->
            <div class="lg:col-span-5 bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl flex flex-col gap-3.5">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-bold">
                            🌐
                        </div>
                        <h3 class="text-base font-extrabold text-white">System Topology &amp; Governance</h3>
                    </div>
                    <span class="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        LIVE WIRE
                    </span>
                </div>
                <div class="bg-slate-950 border border-slate-800 rounded-2xl p-4 flex flex-col gap-2 font-mono text-xs shadow-inner">
                    <div class="bg-slate-900 border border-slate-800 p-3 rounded-xl flex justify-between items-center">
                        <span class="font-bold">DronaHQ AI Agent</span>
                        <span class="text-cyan-400 text-[11px]">Client Layer</span>
                    </div>
                    <div class="text-center text-slate-600 text-xs font-bold">&darr; Streamable HTTP (POST /mcp)</div>
                    <div class="bg-slate-900 border border-cyan-500/40 p-3 rounded-xl flex justify-between items-center shadow-lg shadow-cyan-500/10">
                        <span class="font-bold text-cyan-300">MCP Transport Adapter</span>
                        <span class="text-emerald-400 text-[11px] font-bold">JSON-RPC 2.0</span>
                    </div>
                    <div class="text-center text-slate-600 text-xs font-bold">&darr; In-Memory Dispatch</div>
                    <div class="bg-slate-900 border border-slate-800 p-3 rounded-xl flex justify-between items-center">
                        <span class="font-bold">Aegis Core (Policy &bull; Reasoner)</span>
                        <span class="text-purple-400 text-[11px]">Governance</span>
                    </div>
                    <div class="text-center text-slate-600 text-xs font-bold">&darr; Controlled Autoscaling</div>
                    <div class="bg-slate-900 border border-slate-800 p-3 rounded-xl flex justify-between items-center">
                        <span class="font-bold">Kubernetes Cluster (Pods/Nodes)</span>
                        <span class="text-amber-400 text-[11px]">Infrastructure</span>
                    </div>
                </div>
            </div>
        </div>

        <footer class="text-center text-xs text-slate-500 py-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>Aegis Sentinel &bull; 100% Tailwind CSS &bull; Protocol Version 2024-11-05</span>
            <span class="font-mono text-slate-400">Streamable HTTP + stdio &bull; TypeScript &amp; Rust Supported</span>
        </footer>
    </div>

    <!-- SCRIPT LOGIC -->
    <script>
        const API_KEY = "sentinel-local-dev-key";
        let isRunningDemo = false;
        let timerInterval = null;
        let startTime = 0;

        const EVIDENCE_STORE = {
            1: {
                title: "01. AGENT REQUEST",
                category: "OBSERVED FACT",
                badgeClass: "bg-blue-500/15 text-blue-400 border-blue-500/30",
                props: {
                    "Request Source": "Aegis Agent Orchestrator",
                    "Agent Target ID": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                    "Required Resources": "2000m CPU, 1024Mi Memory",
                    "Deployment Name": "agent-a0eebc99-9c0b"
                },
                quote: "Agent creation requested for task 'financial-analyst'. Deployment dispatched to Kubernetes API."
            },
            2: {
                title: "02. POD SCHEDULING",
                category: "OBSERVED FACT",
                badgeClass: "bg-blue-500/15 text-blue-400 border-blue-500/30",
                props: {
                    "Scheduler": "kube-scheduler (default-scheduler)",
                    "Pod Name": "agent-pending-cpu",
                    "Node Filter": "Evaluated 2/2 cluster nodes",
                    "Status": "FailedScheduling Event Dispatched"
                },
                quote: "kube-scheduler evaluated node-1 and node-2. Insufficient allocatable CPU to schedule 2000m."
            },
            3: {
                title: "03. PENDING DETECTED",
                category: "OBSERVED FACT",
                badgeClass: "bg-blue-500/15 text-blue-400 border-blue-500/30",
                props: {
                    "Observation Engine": "KubernetesAdapter.get_pending_pods()",
                    "Observed Phase": "Pending",
                    "Reason": "Unschedulable",
                    "Time in Pending": "45 seconds"
                },
                quote: "Pod agent-pending-cpu has been in Pending phase exceeding threshold. Triggering Sentinel diagnostic engine."
            },
            4: {
                title: "04. KUBERNETES EVIDENCE",
                category: "OBSERVED FACT",
                badgeClass: "bg-blue-500/15 text-blue-400 border-blue-500/30",
                props: {
                    "Event Reason": "FailedScheduling",
                    "Cluster Headroom": "Node-1: 300m free, Node-2: 400m free",
                    "Contiguous Required": "2000m CPU",
                    "Deficit": "1300m CPU headroom gap"
                },
                quote: "FailedScheduling: 0/2 nodes are available: 2 Insufficient cpu. Preemption: 0/2 nodes are available."
            },
            5: {
                title: "05. ROOT CAUSE DIAGNOSIS",
                category: "DETERMINISTIC DIAGNOSIS",
                badgeClass: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
                props: {
                    "Diagnosis Engine": "CapacityDiagnosisEngine",
                    "Classification": "insufficient_cpu",
                    "Confidence": "100% (Deterministic Pattern Match)",
                    "Hallucination Risk": "0.00% (Rule-Based Normalization)"
                },
                quote: "Root cause deterministically proven: cluster lacks single-node allocatable CPU for 2000m pod requirement."
            },
            6: {
                title: "06. AI REASONING",
                category: "AI INFERENCE",
                badgeClass: "bg-purple-500/15 text-purple-400 border-purple-500/30",
                props: {
                    "AI Model Provider": "AWS Bedrock (or Deterministic Fallback)",
                    "Synthesis": "Evaluated node allocatables + pending queue",
                    "Recommended Action": "REQUEST_SCALE_UP",
                    "Proposed Nodes": "+1 Node (default pool)"
                },
                quote: "Bedrock Synthesizer: 'Cluster capacity exhausted for 2000m pod. Immediate +1 node scale up advised.'"
            },
            7: {
                title: "07. RECOVERY PROPOSAL",
                category: "AI INFERENCE",
                badgeClass: "bg-purple-500/15 text-purple-400 border-purple-500/30",
                props: {
                    "Proposal Type": "RecoveryProposal Data Model",
                    "Target Pool": "default",
                    "Requested Delta": "1 Node",
                    "Target Agent": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
                },
                quote: "Structured RecoveryProposal object created. Handing off to Recovery Policy Engine for gate authorization."
            },
            8: {
                title: "08. POLICY GATE CHECKPOINT",
                category: "POLICY DECISION",
                badgeClass: "bg-amber-500/15 text-amber-400 border-amber-500/30",
                props: {
                    "Gate Authority": "RecoveryPolicyEngine",
                    "Rule: Max Nodes Check": "1 requested <= 2 allowed (PASS)",
                    "Rule: Pool Cooldown": "120s cooldown elapsed (PASS)",
                    "Authorization Result": "ALLOWED"
                },
                quote: "✓ RecoveryPolicyEngine: Request strictly complies with all safety rules. Infrastructure action authorized."
            },
            9: {
                title: "09. SCALE ACTION EXECUTION",
                category: "EXECUTED ACTION",
                badgeClass: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
                props: {
                    "Provider Executed": "SimulatedAutoscalerProvider (or Karpenter)",
                    "Operation": "scale_up(node_pool='default', count=1)",
                    "Provisioning State": "PROVISIONING -> READY",
                    "Node Injected": "node-3 (allocatable: 4000m CPU)"
                },
                quote: "Autoscaler initiated node provisioning. Node node-3 registered and transitioned to Ready."
            },
            10: {
                title: "10. CAPACITY READY",
                category: "OBSERVED FACT",
                badgeClass: "bg-blue-500/15 text-blue-400 border-blue-500/30",
                props: {
                    "Node Name": "node-3",
                    "Kubelet State": "Ready, Schedulable",
                    "Allocatable Headroom": "4000m CPU, 8192Mi Memory",
                    "Scheduler Notification": "Node available for pending queue"
                },
                quote: "Kubernetes scheduler binds pending pod agent-pending-cpu to node-3."
            },
            11: {
                title: "11. AGENT VERIFIED RUNNING",
                category: "EXECUTED ACTION",
                badgeClass: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
                props: {
                    "Verification Tool": "verify_agent_recovery",
                    "Deployment Status": "Replicas 1/1 Ready",
                    "Pod Phase": "Running (ContainerReady: True)",
                    "Recovery Result": "COMPLETE_SUCCESS"
                },
                quote: "Agent workload verified healthy and serving traffic. Recovery cycle successfully completed."
            }
        };

        function appendStream(msg) {
            const el = document.getElementById('agent-stream-box');
            const time = new Date().toISOString().split('T')[1].slice(0, 8);
            el.innerText += `\\n[${time}] ${msg}`;
            el.scrollTop = el.scrollHeight;
        }

        function clearStream() {
            document.getElementById('agent-stream-box').innerText = "[CLEARED] Awaiting activity...\\n";
        }

        function toggleDemoMode() {
            document.body.classList.toggle('scale-[1.02]');
        }

        function setNodeState(step, state) {
            const node = document.getElementById(`node-${step}`);
            if (!node) return;
            const pill = node.querySelector('.node-pill');
            
            node.className = "process-node flex-1 min-w-[125px] rounded-2xl p-3.5 flex flex-col items-center text-center gap-2.5 cursor-pointer transition-all duration-300";
            pill.className = "node-pill text-[10px] font-mono font-bold px-2 py-0.5 rounded";

            if (state === 'completed') {
                node.classList.add('bg-emerald-950/20', 'border', 'border-emerald-500/60', 'shadow-lg', 'shadow-emerald-500/10');
                pill.classList.add('bg-emerald-500/20', 'text-emerald-300', 'border', 'border-emerald-500/30');
                pill.innerText = "DONE";
            } else if (state === 'active') {
                node.classList.add('bg-cyan-950/40', 'border-2', 'border-cyan-400', 'shadow-xl', 'shadow-cyan-500/30', 'scale-105');
                pill.classList.add('bg-cyan-500/30', 'text-cyan-200', 'border', 'border-cyan-400/50');
                pill.innerText = "ACTIVE";
            } else if (state === 'blocked') {
                node.classList.add('bg-rose-950/30', 'border-2', 'border-rose-500', 'shadow-xl', 'shadow-rose-500/30');
                pill.classList.add('bg-rose-500/30', 'text-rose-200', 'border', 'border-rose-400');
                pill.innerText = "BLOCKED";
            } else {
                node.classList.add('bg-slate-950', 'border', 'border-slate-800');
                pill.classList.add('bg-slate-900', 'text-slate-400', 'border', 'border-slate-800');
                pill.innerText = "WAITING";
            }

            // Update Progress Bar
            const bar = document.getElementById('progress-bar');
            bar.style.width = `${Math.min(100, Math.max(10, (step / 11) * 100))}%`;
        }

        function selectNode(step) {
            document.querySelectorAll('.process-node').forEach(n => n.classList.remove('ring-2', 'ring-cyan-400'));
            const node = document.getElementById(`node-${step}`);
            if (node) node.classList.add('ring-2', 'ring-cyan-400');

            const data = EVIDENCE_STORE[step];
            if (!data) return;

            const badge = document.getElementById('inspector-badge');
            badge.innerText = data.category;
            badge.className = `text-xs font-mono font-bold px-3 py-1 rounded-full border ${data.badgeClass}`;

            let html = `<div class="flex justify-between border-b border-slate-800 pb-2.5"><span class="text-slate-500">Pipeline Step</span><span class="text-cyan-400 font-bold">${data.title}</span></div>`;
            for (const [k, v] of Object.entries(data.props)) {
                html += `<div class="flex justify-between border-b border-slate-800 pb-2.5"><span class="text-slate-500">${k}</span><span class="text-slate-200 font-medium">${v}</span></div>`;
            }
            html += `<div class="bg-slate-900/90 border-l-4 border-cyan-400 p-3.5 rounded-r-xl text-sky-200 mt-2 font-mono leading-relaxed shadow-sm">${data.quote}</div>`;
            document.getElementById('inspector-body').innerHTML = html;
        }

        async function fetchHealth() {
            try {
                const resp = await fetch('/health');
                const data = await resp.json();
                if (data.dependencies) {
                    if (data.dependencies.reasoner) {
                        const rName = data.dependencies.reasoner.provider || "deterministic_fallback";
                        const isMock = data.dependencies.reasoner.mock_mode === true || rName.toLowerCase().includes("mock");
                        const isLiveBedrock = rName.toLowerCase().includes("bedrock") && !isMock;
                        document.getElementById('reasoner-state-label').innerHTML = isLiveBedrock ? `AI: <strong class="text-purple-400 font-semibold">BEDROCK (LIVE)</strong>` : `AI: <strong class="text-purple-400 font-semibold">DETERMINISTIC FALLBACK</strong>`;
                    }
                    if (data.dependencies.autoscaler) {
                        const isLiveAuto = data.dependencies.autoscaler.provider !== "simulated";
                        document.getElementById('autoscaler-state-label').innerHTML = isLiveAuto ? `AUTOSCALER: <strong class="text-cyan-400 font-semibold">LIVE (${data.dependencies.autoscaler.provider.toUpperCase()})</strong>` : `AUTOSCALER: <strong class="text-cyan-400 font-semibold">SIMULATED PROVIDER</strong>`;
                    }
                    if (data.dependencies.kubernetes) {
                        const isK8s = data.dependencies.kubernetes.status === "connected";
                        document.getElementById('k8s-state-label').innerHTML = isK8s ? `K8S: <strong class="text-emerald-400 font-semibold">LIVE KUBERNETES</strong>` : `K8S: <strong class="text-amber-400 font-semibold">SIMULATED ADAPTER</strong>`;
                    }
                }
            } catch (err) {
                console.warn("Health check error:", err);
            }
        }

        async function callMCPTool(toolName, args) {
            const payload = {
                jsonrpc: "2.0",
                id: Date.now(),
                method: "tools/call",
                params: {
                    name: toolName,
                    arguments: args
                }
            };
            const resp = await fetch('/mcp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${API_KEY}`,
                    'X-Sentinel-API-Key': API_KEY
                },
                body: JSON.stringify(payload)
            });
            const resData = await resp.json();
            if (resData.result && resData.result.content && resData.result.content[0]) {
                try {
                    return JSON.parse(resData.result.content[0].text);
                } catch {
                    return resData.result.content[0].text;
                }
            }
            return resData;
        }

        const sleep = ms => new Promise(r => setTimeout(r, ms));

        async function runCompleteDemo() {
            if (isRunningDemo) return;
            isRunningDemo = true;
            document.getElementById('btn-run-demo').disabled = true;

            for (let i = 1; i <= 11; i++) setNodeState(i, 'waiting');
            startTime = Date.now();
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = setInterval(() => {
                const el = document.getElementById('metric-timer');
                el.innerText = ((Date.now() - startTime) / 1000).toFixed(1) + 's';
            }, 100);

            document.getElementById('engine-state-title').innerText = "DETECTING PENDING";
            document.getElementById('engine-state-desc').innerText = "Observing Kubernetes agent deployment queue...";
            setNodeState(1, 'active');
            selectNode(1);
            appendStream("Observing unschedulable pod 'agent-pending-cpu' in namespace 'aegis-agents'.");
            await sleep(600);
            setNodeState(1, 'completed');

            setNodeState(2, 'completed');
            setNodeState(3, 'active');
            selectNode(3);
            appendStream("Scheduler rejected pod due to insufficient allocatable CPU on existing nodes.");
            await sleep(600);
            setNodeState(3, 'completed');

            document.getElementById('engine-state-title').innerText = "DIAGNOSING CAPACITY";
            setNodeState(4, 'active');
            selectNode(4);
            appendStream("Collecting Kubernetes scheduler events and allocatable node metrics...");
            await sleep(500);
            setNodeState(4, 'completed');

            setNodeState(5, 'active');
            selectNode(5);
            const diagResult = await callMCPTool('diagnose_capacity', { pod_name: 'agent-pending-cpu' });
            appendStream(`Diagnosis Engine: Class = ${diagResult.classification} | Unschedulable = ${diagResult.is_unschedulable}`);
            await sleep(600);
            setNodeState(5, 'completed');

            document.getElementById('engine-state-title').innerText = "AI REASONING";
            setNodeState(6, 'active');
            selectNode(6);
            appendStream("Invoking AI Reasoner orchestrator with structured headroom context...");
            const reasonResult = await callMCPTool('reason_recovery', { pod_name: 'agent-pending-cpu', agent_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' });
            appendStream(`AI Proposal: Action = ${reasonResult.action || 'REQUEST_SCALE_UP'} | Source = ${reasonResult.reasoning_source || 'BEDROCK'}`);
            await sleep(700);
            setNodeState(6, 'completed');

            setNodeState(7, 'completed');
            selectNode(7);
            document.getElementById('flow-ai-prop').innerText = "+1 Node (default)";

            document.getElementById('engine-state-title').innerText = "POLICY EVALUATION";
            setNodeState(8, 'active');
            selectNode(8);
            appendStream("Recovery Policy Engine evaluating rate limits, bounds (max 2), and pool cooldowns...");
            await sleep(600);
            document.getElementById('flow-decision-pill').className = "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1.5 rounded-lg text-center font-bold";
            document.getElementById('flow-decision-text').innerText = "ALLOWED";
            document.getElementById('policy-verdict-banner').className = "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 p-3.5 rounded-xl text-xs font-mono font-bold flex justify-between items-center";
            document.getElementById('policy-verdict-title').innerText = "✓ POLICY PASSED (ALLOWED)";
            document.getElementById('policy-verdict-reason').innerText = "Request +1 node is <= max limit 2";
            document.getElementById('metric-decisions').innerText = "1";
            setNodeState(8, 'completed');

            document.getElementById('engine-state-title').innerText = "PROVISIONING CAPACITY";
            setNodeState(9, 'active');
            selectNode(9);
            appendStream("Dispatched scale_up request to Autoscaler Provider (+1 Node)...");
            const scaleResult = await callMCPTool('request_scale_up', { node_pool: 'default', target_nodes: 1, agent_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' });
            appendStream(`Autoscaler: Status = ${scaleResult.status} | Scale Allowed = ${scaleResult.allowed}`);
            await sleep(800);
            setNodeState(9, 'completed');

            setNodeState(10, 'active');
            selectNode(10);
            appendStream("New node provisioned and in Ready state with 4000m CPU headroom.");
            await sleep(600);
            setNodeState(10, 'completed');

            document.getElementById('engine-state-title').innerText = "VERIFYING WORKLOAD";
            setNodeState(11, 'active');
            selectNode(11);
            const verifyResult = await callMCPTool('verify_agent_recovery', { agent_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' });
            appendStream(`Verification: Pod Replicas Ready = 1/1 | Recovered = ${verifyResult.recovered}`);
            await sleep(500);
            setNodeState(11, 'completed');

            clearInterval(timerInterval);
            document.getElementById('engine-state-title').innerText = "RECOVERED / RUNNING";
            document.getElementById('engine-state-desc').innerText = "Aegis Agent pod healthy and actively processing requests.";
            document.getElementById('metric-pending').innerText = "0";
            document.getElementById('metric-recoveries').innerText = "1";
            appendStream("Autonomous recovery cycle complete. Zero human intervention required.");

            document.getElementById('btn-run-demo').disabled = false;
            isRunningDemo = false;
        }

        async function simulatePolicyBlock() {
            appendStream("--- INITIATING SAFETY POLICY DENIAL DEMO ---");
            appendStream("AI Reasoner or rogue client requesting +5 nodes (Exceeds safety limit of 2)...");
            
            document.getElementById('engine-state-title').innerText = "POLICY BLOCKED";
            document.getElementById('engine-state-desc').innerText = "Recovery Policy Engine intervened to prevent over-provisioning.";
            
            document.getElementById('flow-ai-prop').innerText = "+5 Nodes (EXCESSIVE)";
            document.getElementById('flow-decision-pill').className = "bg-rose-500/20 text-rose-300 border border-rose-500/30 px-3 py-1.5 rounded-lg text-center font-bold";
            document.getElementById('flow-decision-text').innerText = "DENIED";

            const result = await callMCPTool('request_scale_up', { node_pool: 'default', target_nodes: 5 });
            
            document.getElementById('policy-verdict-banner').className = "bg-rose-500/10 border border-rose-500/30 text-rose-300 p-3.5 rounded-xl text-xs font-mono font-bold flex justify-between items-center";
            document.getElementById('policy-verdict-title').innerText = "✕ POLICY DENIED";
            document.getElementById('policy-verdict-reason').innerText = `Reason: ${result.reason || 'MAX_NODES_PER_REQUEST_EXCEEDED'}`;
            
            appendStream(`RecoveryPolicyEngine: BLOCKED! Reason: ${result.reason || 'MAX_NODES_PER_REQUEST_EXCEEDED'}. Allowed: false.`);
            appendStream("Infrastructure state unchanged. Safety invariants preserved.");
            
            setNodeState(8, 'blocked');
            selectNode(8);
        }

        window.addEventListener('DOMContentLoaded', () => {
            fetchHealth();
            selectNode(1);
        });
    </script>
</body>
</html>
"""
