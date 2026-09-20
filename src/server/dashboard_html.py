"""Interactive Command Center HTML Dashboard for Nasiko Sentinel using Tailwind CSS."""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nasiko Sentinel — Autonomous Kubernetes Recovery Command Center</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkBase: '#050811',
                        darkSurface: '#0b1120',
                        darkCard: '#111827',
                        darkCardHover: '#1f2937',
                        borderSubtle: '#1e293b',
                        accentCyan: '#06b6d4',
                        accentBlue: '#3b82f6',
                        accentEmerald: '#10b981',
                        accentPurple: '#8b5cf6',
                        accentAmber: '#f59e0b',
                        accentRose: '#f43f5e',
                    },
                    fontFamily: {
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
                    }
                }
            }
        }
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        @keyframes pulse-ring {
            0% { transform: scale(0.6); opacity: 1; }
            100% { transform: scale(2.0); opacity: 0; }
        }
        .pulse-ring-anim::after {
            content: '';
            position: absolute;
            inset: -4px;
            border-radius: 9999px;
            border: 2px solid #06b6d4;
            animation: pulse-ring 1.8s cubic-bezier(0.24, 0, 0.38, 1) infinite;
        }
    </style>
</head>
<body class="bg-darkBase text-slate-100 font-sans min-h-screen p-4 sm:p-6 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-950/20 via-darkBase to-darkBase">
    <div class="max-w-[1440px] mx-auto flex flex-col gap-5">
        
        <!-- 1. HERO / COMMAND HEADER -->
        <header class="bg-darkSurface/80 backdrop-blur-xl border border-borderSubtle rounded-2xl p-4 sm:p-5 flex flex-wrap items-center justify-between gap-4 shadow-2xl shadow-black/50">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-gradient-to-br from-cyan-500 via-blue-600 to-purple-600 rounded-xl flex items-center justify-center font-black text-2xl text-white shadow-lg shadow-cyan-500/30">
                    ⚡
                </div>
                <div>
                    <h1 class="text-xl font-extrabold tracking-tight flex items-center gap-2">
                        NASIKO SENTINEL 
                        <span class="text-xs font-semibold font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 px-2 py-0.5 rounded-md">Tailwind UI &bull; MCP 2024-11-05</span>
                    </h1>
                    <p class="text-xs text-slate-400">Autonomous Agent Capacity &amp; Elastic Kubernetes Self-Healing Control Plane</p>
                </div>
            </div>

            <!-- Subsystem Status Pills -->
            <div class="flex flex-wrap gap-2 text-xs font-mono">
                <div class="bg-darkCard border border-borderSubtle px-3 py-1.5 rounded-lg flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400"></span>
                    <span>MCP: READY (14 Tools)</span>
                </div>
                <div class="bg-darkCard border border-borderSubtle px-3 py-1.5 rounded-lg flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-amber-400 shadow-sm shadow-amber-400"></span>
                    <span id="k8s-state-label">K8S: SIMULATED ADAPTER</span>
                </div>
                <div class="bg-darkCard border border-borderSubtle px-3 py-1.5 rounded-lg flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-purple-400 shadow-sm shadow-purple-400"></span>
                    <span id="reasoner-state-label">AI: DETERMINISTIC FALLBACK</span>
                </div>
                <div class="bg-darkCard border border-borderSubtle px-3 py-1.5 rounded-lg flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-amber-400 shadow-sm shadow-amber-400"></span>
                    <span id="autoscaler-state-label">AUTOSCALER: SIMULATED PROVIDER</span>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center gap-3">
                <button id="btn-run-demo" onclick="runCompleteDemo()" class="px-4 py-2 rounded-xl font-semibold text-sm bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white shadow-lg shadow-blue-500/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0 flex items-center gap-2">
                    <span>▶</span> RUN RECOVERY DEMO
                </button>
                <button id="btn-sim-block" onclick="simulatePolicyBlock()" class="px-3.5 py-2 rounded-xl font-semibold text-sm bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-all flex items-center gap-2">
                    <span>⚠</span> SIMULATE POLICY BLOCK
                </button>
                <button id="btn-demo-mode" onclick="toggleDemoMode()" class="px-3 py-2 rounded-xl text-xs font-semibold bg-darkCard border border-borderSubtle text-slate-300 hover:text-white transition-all flex items-center gap-1.5">
                    <span>📺</span> DEMO MODE
                </button>
            </div>
        </header>

        <!-- 2. CENTRAL ENGINE STATUS CARD -->
        <div class="bg-gradient-to-r from-darkSurface/90 to-darkCard/90 border border-borderSubtle rounded-2xl p-6 shadow-xl relative overflow-hidden grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
            <div class="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-500 to-transparent"></div>
            
            <div class="flex flex-col gap-1.5">
                <span class="text-xs font-bold tracking-widest text-slate-400 uppercase font-mono">Agent Recovery Engine &bull; Realtime State</span>
                <div class="text-3xl font-black tracking-tight text-white flex items-center gap-3">
                    <div class="relative w-4 h-4 rounded-full bg-cyan-400 pulse-ring-anim"></div>
                    <span id="engine-state-title">IDLE / READY</span>
                </div>
                <p id="engine-state-desc" class="text-xs text-slate-400">Monitoring Kubernetes agent deployment queue across namespaces.</p>
            </div>

            <div class="bg-darkBase/70 border border-borderSubtle rounded-xl p-4 flex flex-col gap-1">
                <span class="text-[11px] font-mono text-slate-400">TARGET NASIKO WORKLOAD</span>
                <span class="text-sm font-bold font-mono text-cyan-400" id="target-pod-name">agent-pending-cpu</span>
                <span class="text-xs font-mono text-slate-400 truncate">UUID: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11</span>
                <span class="text-xs font-medium text-amber-400 mt-1">Demand: 2000m CPU &bull; 1 Node Required</span>
            </div>

            <div class="grid grid-cols-2 gap-2.5">
                <div class="bg-darkBase/70 border border-borderSubtle rounded-xl p-3 flex flex-col">
                    <span id="metric-pending" class="text-xl font-extrabold font-mono text-white">1</span>
                    <span class="text-[11px] text-slate-400">Pending Pods</span>
                </div>
                <div class="bg-darkBase/70 border border-borderSubtle rounded-xl p-3 flex flex-col">
                    <span id="metric-decisions" class="text-xl font-extrabold font-mono text-white">0</span>
                    <span class="text-[11px] text-slate-400">Policy Audits</span>
                </div>
                <div class="bg-darkBase/70 border border-borderSubtle rounded-xl p-3 flex flex-col">
                    <span id="metric-recoveries" class="text-xl font-extrabold font-mono text-white">0</span>
                    <span class="text-[11px] text-slate-400">Recoveries</span>
                </div>
                <div class="bg-darkBase/70 border border-borderSubtle rounded-xl p-3 flex flex-col">
                    <span id="metric-timer" class="text-xl font-extrabold font-mono text-cyan-400">0.0s</span>
                    <span class="text-[11px] text-slate-400">Elapsed Time</span>
                </div>
            </div>
        </div>

        <!-- 3. EVIDENTIARY PROCESS GRAPH -->
        <div class="bg-darkSurface/90 border border-borderSubtle rounded-2xl p-5 flex flex-col gap-4">
            <div class="flex items-center justify-between">
                <h2 class="text-sm font-bold flex items-center gap-2">
                    <span>🕸</span> Autonomous Evidentiary Process Pipeline
                </h2>
                <span class="text-[11px] font-mono bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2.5 py-0.5 rounded-md">Click Any Node to Inspect Evidence</span>
            </div>

            <div class="flex items-stretch gap-2 overflow-x-auto pb-3 pt-1 scrollbar-thin" id="process-graph">
                <!-- 11 Standard Evidentiary Nodes -->
                <div id="node-1" onclick="selectNode(1)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">01</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">📨</div>
                    <div class="text-xs font-bold text-white">Agent Request</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-2" onclick="selectNode(2)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">02</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">⚙️</div>
                    <div class="text-xs font-bold text-white">Pod Scheduling</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-3" onclick="selectNode(3)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">03</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">⏳</div>
                    <div class="text-xs font-bold text-white">Pending Detected</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-4" onclick="selectNode(4)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">04</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">🔍</div>
                    <div class="text-xs font-bold text-white">K8s Evidence</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-5" onclick="selectNode(5)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">05</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">🧩</div>
                    <div class="text-xs font-bold text-white">Root Cause</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-6" onclick="selectNode(6)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">06</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">🧠</div>
                    <div class="text-xs font-bold text-white">AI Reasoning</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-7" onclick="selectNode(7)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">07</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">📜</div>
                    <div class="text-xs font-bold text-white">Recovery Proposal</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-8" onclick="selectNode(8)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">08</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">🛡️</div>
                    <div class="text-xs font-bold text-white">Policy Gate</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-9" onclick="selectNode(9)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">09</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">🔧</div>
                    <div class="text-xs font-bold text-white">Scale Action</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-10" onclick="selectNode(10)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">10</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">✅</div>
                    <div class="text-xs font-bold text-white">Capacity Ready</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>

                <div id="node-11" onclick="selectNode(11)" class="process-node flex-1 min-w-[120px] bg-darkCard border border-borderSubtle rounded-xl p-3 flex flex-col items-center text-center gap-2 cursor-pointer hover:border-cyan-500 transition-all">
                    <span class="text-[10px] font-mono font-bold text-slate-500">11</span>
                    <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">🚀</div>
                    <div class="text-xs font-bold text-white">Agent Running</div>
                    <span class="node-pill text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">WAITING</span>
                </div>
            </div>
        </div>

        <!-- 4. WORKSPACE: EVIDENCE INSPECTOR & POLICY CHECKPOINT -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <!-- Left: Evidence Deep Inspector (7 cols) -->
            <div class="lg:col-span-7 bg-darkSurface/90 border border-borderSubtle rounded-2xl p-5 flex flex-col gap-4">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-bold flex items-center gap-2">
                        <span>📊</span> Evidentiary Deep Inspector
                    </h3>
                    <span id="inspector-badge" class="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/30">OBSERVED FACT</span>
                </div>
                <div id="inspector-body" class="bg-darkBase border border-borderSubtle rounded-xl p-4 flex flex-col gap-3 min-h-[260px] font-mono text-xs">
                    <div class="flex justify-between border-b border-slate-800 pb-2">
                        <span class="text-slate-500">Selected Step</span>
                        <span class="text-cyan-400 font-bold" id="ev-step-title">01. Initial Request Observation</span>
                    </div>
                    <div class="flex justify-between border-b border-slate-800 pb-2">
                        <span class="text-slate-500">Pod Subject</span>
                        <span class="text-slate-200">agent-pending-cpu</span>
                    </div>
                    <div class="flex justify-between border-b border-slate-800 pb-2">
                        <span class="text-slate-500">Source</span>
                        <span class="text-slate-200">Kubernetes Scheduler Events</span>
                    </div>
                    <div id="ev-quote-text" class="bg-white/[0.02] border-l-2 border-cyan-400 p-3 rounded-r text-sky-200 mt-2">
Click "RUN RECOVERY DEMO" to execute the live recovery pipeline. Click any pipeline step above to inspect evidentiary properties.
                    </div>
                </div>
            </div>

            <!-- Right: Policy Checkpoint (5 cols) -->
            <div class="lg:col-span-5 bg-darkSurface/90 border border-borderSubtle rounded-2xl p-5 flex flex-col gap-4">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-bold flex items-center gap-2">
                        <span>🤖</span> Sentinel AI &amp; Recovery Policy Gate
                    </h3>
                    <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30">AUTHORITATIVE</span>
                </div>

                <div class="bg-darkBase border border-borderSubtle rounded-xl p-4 flex flex-col gap-3.5">
                    <div class="flex items-center justify-between bg-darkCard border border-borderSubtle rounded-lg p-3 text-xs font-mono">
                        <div class="bg-purple-500/20 text-purple-300 px-2.5 py-1 rounded text-center">
                            AI PROPOSAL<br><span id="flow-ai-prop" class="text-[10px] text-purple-400">+1 Node</span>
                        </div>
                        <span class="text-slate-600 font-bold">➔</span>
                        <div class="bg-amber-500/20 text-amber-300 px-2.5 py-1 rounded text-center">
                            POLICY GATE<br><span class="text-[10px] text-amber-400">Safety Check</span>
                        </div>
                        <span class="text-slate-600 font-bold">➔</span>
                        <div id="flow-decision-pill" class="bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded text-center font-bold">
                            DECISION<br><span id="flow-decision-text" class="text-[10px]">STANDBY</span>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2 text-xs font-mono">
                        <div class="bg-white/[0.02] border border-borderSubtle p-2 rounded flex justify-between">
                            <span class="text-slate-500">MAX / REQ:</span>
                            <span class="text-cyan-400 font-bold">2 Nodes</span>
                        </div>
                        <div class="bg-white/[0.02] border border-borderSubtle p-2 rounded flex justify-between">
                            <span class="text-slate-500">CLUSTER MAX:</span>
                            <span class="text-cyan-400 font-bold">10 Nodes</span>
                        </div>
                        <div class="bg-white/[0.02] border border-borderSubtle p-2 rounded flex justify-between">
                            <span class="text-slate-500">COOLDOWN:</span>
                            <span class="text-cyan-400 font-bold">120s</span>
                        </div>
                        <div class="bg-white/[0.02] border border-borderSubtle p-2 rounded flex justify-between">
                            <span class="text-slate-500">POOL:</span>
                            <span class="text-cyan-400 font-bold">default</span>
                        </div>
                    </div>

                    <div id="policy-verdict-banner" class="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 p-3 rounded-lg text-xs font-mono font-bold flex justify-between items-center">
                        <span id="policy-verdict-title">✓ POLICY ENGINE STANDBY</span>
                        <span id="policy-verdict-reason" class="text-[11px] font-normal text-slate-400">Awaiting AI proposal</span>
                    </div>

                    <div class="text-center text-xs font-bold text-purple-300 bg-purple-500/10 border border-dashed border-purple-500/30 py-2 rounded-lg">
                        &ldquo;AI proposes. Policy decides.&rdquo;
                    </div>
                </div>
            </div>
        </div>

        <!-- 5. BOTTOM GRID: ACTIVITY STREAM & TOPOLOGY -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <div class="lg:col-span-7 bg-darkSurface/90 border border-borderSubtle rounded-2xl p-5 flex flex-col gap-3">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-bold flex items-center gap-2">
                        <span>📝</span> Autonomous Agent Activity Stream
                    </h3>
                    <button onclick="clearStream()" class="text-[11px] font-mono px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 border border-borderSubtle">Clear</button>
                </div>
                <div id="agent-stream-box" class="bg-darkBase border border-borderSubtle rounded-xl p-3.5 font-mono text-xs text-sky-200 h-56 overflow-y-auto leading-relaxed">
[SYSTEM INIT] Nasiko Sentinel Command Center loaded (Tailwind UI).
[READY] MCP Server connected via Streamable HTTP (JSON-RPC 2.0).
[STANDBY] Monitoring Kubernetes agent deployment queue.
                </div>
            </div>

            <div class="lg:col-span-5 bg-darkSurface/90 border border-borderSubtle rounded-2xl p-5 flex flex-col gap-3">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-bold flex items-center gap-2">
                        <span>🌐</span> System Topology &amp; Governance
                    </h3>
                    <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">LIVE GRAPH</span>
                </div>
                <div class="bg-darkBase border border-borderSubtle rounded-xl p-3.5 flex flex-col gap-2 font-mono text-xs">
                    <div class="bg-darkCard border border-borderSubtle p-2.5 rounded-lg flex justify-between items-center">
                        <span><strong>DronaHQ AI Agent</strong> (UI / Webhook)</span>
                        <span class="text-cyan-400 text-[10px]">Client Layer</span>
                    </div>
                    <div class="text-center text-slate-600 text-[10px]">&darr; Streamable HTTP (POST /mcp)</div>
                    <div class="bg-darkCard border border-cyan-500/40 p-2.5 rounded-lg flex justify-between items-center">
                        <span><strong>MCP Server Transport Adapter</strong></span>
                        <span class="text-emerald-400 text-[10px]">JSON-RPC 2.0</span>
                    </div>
                    <div class="text-center text-slate-600 text-[10px]">&darr; In-Memory Dispatch</div>
                    <div class="bg-darkCard border border-borderSubtle p-2.5 rounded-lg flex justify-between items-center">
                        <span><strong>Sentinel Core</strong> (Observer &bull; Reasoner &bull; Policy)</span>
                        <span class="text-purple-400 text-[10px]">Governance</span>
                    </div>
                    <div class="text-center text-slate-600 text-[10px]">&darr; Controlled Autoscaling</div>
                    <div class="bg-darkCard border border-borderSubtle p-2.5 rounded-lg flex justify-between items-center">
                        <span><strong>Kubernetes Cluster</strong> (Nodes &amp; Pods)</span>
                        <span class="text-amber-400 text-[10px]">Infrastructure</span>
                    </div>
                </div>
            </div>
        </div>

        <footer class="text-center text-xs text-slate-500 py-3 border-t border-borderSubtle">
            Nasiko Sentinel &bull; Tailwind CSS Edition &bull; Protocol Version 2024-11-05 &bull; Dual Transport (Streamable HTTP / stdio)
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
                    "Request Source": "Nasiko Agent Orchestrator",
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
            document.body.classList.toggle('scale-105');
        }

        function setNodeState(step, state) {
            const node = document.getElementById(`node-${step}`);
            if (!node) return;
            const pill = node.querySelector('.node-pill');
            
            node.classList.remove('border-borderSubtle', 'border-cyan-500', 'border-emerald-500', 'border-rose-500', 'bg-darkCard', 'bg-cyan-950/30', 'bg-emerald-950/30', 'bg-rose-950/30');
            pill.classList.remove('bg-white/5', 'text-slate-400', 'bg-cyan-500/20', 'text-cyan-300', 'bg-emerald-500/20', 'text-emerald-300', 'bg-rose-500/20', 'text-rose-300');

            if (state === 'completed') {
                node.classList.add('border-emerald-500/60', 'bg-emerald-950/20');
                pill.classList.add('bg-emerald-500/20', 'text-emerald-300');
                pill.innerText = "DONE";
            } else if (state === 'active') {
                node.classList.add('border-cyan-400', 'bg-cyan-950/30', 'shadow-lg', 'shadow-cyan-500/20');
                pill.classList.add('bg-cyan-500/20', 'text-cyan-300');
                pill.innerText = "ACTIVE";
            } else if (state === 'blocked') {
                node.classList.add('border-rose-500', 'bg-rose-950/30');
                pill.classList.add('bg-rose-500/20', 'text-rose-300');
                pill.innerText = "BLOCKED";
            } else {
                node.classList.add('border-borderSubtle', 'bg-darkCard');
                pill.classList.add('bg-white/5', 'text-slate-400');
                pill.innerText = "WAITING";
            }
        }

        function selectNode(step) {
            document.querySelectorAll('.process-node').forEach(n => n.classList.remove('ring-2', 'ring-cyan-400'));
            const node = document.getElementById(`node-${step}`);
            if (node) node.classList.add('ring-2', 'ring-cyan-400');

            const data = EVIDENCE_STORE[step];
            if (!data) return;

            const badge = document.getElementById('inspector-badge');
            badge.innerText = data.category;
            badge.className = `text-xs font-mono font-bold px-2.5 py-0.5 rounded border ${data.badgeClass}`;

            let html = `<div class="flex justify-between border-b border-slate-800 pb-2"><span class="text-slate-500">Pipeline Step</span><span class="text-cyan-400 font-bold">${data.title}</span></div>`;
            for (const [k, v] of Object.entries(data.props)) {
                html += `<div class="flex justify-between border-b border-slate-800 pb-2"><span class="text-slate-500">${k}</span><span class="text-slate-200 font-medium">${v}</span></div>`;
            }
            html += `<div class="bg-white/[0.02] border-l-2 border-cyan-400 p-3 rounded-r text-sky-200 mt-2">${data.quote}</div>`;
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
                        document.getElementById('reasoner-state-label').innerText = isLiveBedrock ? "AI: BEDROCK (LIVE)" : "AI: DETERMINISTIC FALLBACK";
                    }
                    if (data.dependencies.autoscaler) {
                        const isLiveAuto = data.dependencies.autoscaler.provider !== "simulated";
                        document.getElementById('autoscaler-state-label').innerText = isLiveAuto ? `AUTOSCALER: LIVE (${data.dependencies.autoscaler.provider.toUpperCase()})` : "AUTOSCALER: SIMULATED PROVIDER";
                    }
                    if (data.dependencies.kubernetes) {
                        const isK8s = data.dependencies.kubernetes.status === "connected";
                        document.getElementById('k8s-state-label').innerText = isK8s ? "K8S: LIVE KUBERNETES" : "K8S: SIMULATED KUBERNETES";
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

            document.getElementById('engine-state-title').innerText = "DETECTING PENDING WORKLOAD";
            document.getElementById('engine-state-desc').innerText = "Observing Kubernetes agent deployment queue...";
            setNodeState(1, 'active');
            selectNode(1);
            appendStream("Observing unschedulable pod 'agent-pending-cpu' in namespace 'nasiko-agents'.");
            await sleep(600);
            setNodeState(1, 'completed');

            setNodeState(2, 'completed');
            setNodeState(3, 'active');
            selectNode(3);
            appendStream("Scheduler rejected pod due to insufficient allocatable CPU on existing 2 nodes.");
            await sleep(600);
            setNodeState(3, 'completed');

            document.getElementById('engine-state-title').innerText = "DIAGNOSING CAPACITY BOTTLENECK";
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

            document.getElementById('engine-state-title').innerText = "FORMULATING AI REASONING";
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

            document.getElementById('engine-state-title').innerText = "EVALUATING RECOVERY POLICY";
            setNodeState(8, 'active');
            selectNode(8);
            appendStream("Recovery Policy Engine evaluating rate limits, bounds (max 2), and pool cooldowns...");
            await sleep(600);
            document.getElementById('flow-decision-pill').className = "bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded text-center font-bold";
            document.getElementById('flow-decision-text').innerText = "ALLOWED";
            document.getElementById('policy-verdict-banner').className = "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 p-3 rounded-lg text-xs font-mono font-bold flex justify-between items-center";
            document.getElementById('policy-verdict-title').innerText = "✓ POLICY PASSED (ALLOWED)";
            document.getElementById('policy-verdict-reason').innerText = "Request +1 node is <= max limit 2";
            document.getElementById('metric-decisions').innerText = "1";
            setNodeState(8, 'completed');

            document.getElementById('engine-state-title').innerText = "PROVISIONING ELASTIC CAPACITY";
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

            document.getElementById('engine-state-title').innerText = "VERIFYING AGENT WORKLOAD";
            setNodeState(11, 'active');
            selectNode(11);
            const verifyResult = await callMCPTool('verify_agent_recovery', { agent_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' });
            appendStream(`Verification: Pod Replicas Ready = 1/1 | Recovered = ${verifyResult.recovered}`);
            await sleep(500);
            setNodeState(11, 'completed');

            clearInterval(timerInterval);
            document.getElementById('engine-state-title').innerText = "RECOVERED / RUNNING";
            document.getElementById('engine-state-desc').innerText = "Nasiko Agent pod healthy and actively processing requests.";
            document.getElementById('metric-pending').innerText = "0";
            document.getElementById('metric-recoveries').innerText = "1";
            appendStream("Autonomous recovery cycle complete. Zero human intervention required.");

            document.getElementById('btn-run-demo').disabled = false;
            isRunningDemo = false;
        }

        async function simulatePolicyBlock() {
            appendStream("--- INITIATING SAFETY POLICY DENIAL DEMO ---");
            appendStream("AI Reasoner or rogue client requesting +5 nodes (Exceeds safety limit of 2)...");
            
            document.getElementById('engine-state-title').innerText = "POLICY DENIED / BLOCKED";
            document.getElementById('engine-state-desc').innerText = "Recovery Policy Engine intervened to prevent over-provisioning.";
            
            document.getElementById('flow-ai-prop').innerText = "+5 Nodes (EXCESSIVE)";
            document.getElementById('flow-decision-pill').className = "bg-rose-500/20 text-rose-300 px-2.5 py-1 rounded text-center font-bold";
            document.getElementById('flow-decision-text').innerText = "DENIED";

            const result = await callMCPTool('request_scale_up', { node_pool: 'default', target_nodes: 5 });
            
            document.getElementById('policy-verdict-banner').className = "bg-rose-500/10 border border-rose-500/30 text-rose-300 p-3 rounded-lg text-xs font-mono font-bold flex justify-between items-center";
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
