"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { GitFork } from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────────
interface Letter {
  char: string;
  x: number;
  y: number;
  baseY: number;
  vx: number;
  vy: number;
  phase: number;   // phase offset for sine bounce
  size: number;
}

interface Sparkle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;     // 0–1, counts down
  maxLife: number;
  size: number;
  hue: number;
}

// ── Footer component ───────────────────────────────────────────────────────────
export function Footer() {
  const canvasRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Typed minimally — we only ever call .remove() on cleanup
    let p5Instance: { remove: () => void } | null = null;

    async function init() {
      const P5 = (await import("p5")).default;

      const sketch = (p: InstanceType<typeof P5>) => {
        const LABEL = "Built by Emmi Dev";
        const BOUNCE_AMP = 6;       // px amplitude for letter bounce
        const BOUNCE_SPEED = 0.04;  // radians per frame
        const SPARKLE_RATE = 3;     // sparkles spawned per frame while animating
        const FONT_SIZE = 18;
        const WORD_GAP = 8;         // extra px between words

        let letters: Letter[] = [];
        let sparkles: Sparkle[] = [];
        let canvasW = 0;

        function buildLetters() {
          letters = [];
          p.textSize(FONT_SIZE);
          p.textFont("monospace");
          p.textStyle(p.BOLD);
          // calculate total width including extra word gaps
          let totalW = 0;
          const chars = Array.from(LABEL);
          for (let i = 0; i < chars.length; i++) {
            totalW += p.textWidth(chars[i]);
            if (chars[i] === " " && i < chars.length - 1) totalW += WORD_GAP;
          }
          let cx = canvasW / 2 - totalW / 2;
          const cy = p.height / 2;
          for (const char of LABEL) {
            const cw = p.textWidth(char);
            letters.push({
              char,
              x: cx + cw / 2,
              y: cy,
              baseY: cy,
              vx: 0,
              vy: 0,
              phase: Math.random() * Math.PI * 2,
              size: FONT_SIZE,
            });
            cx += cw;
            if (char === " ") cx += WORD_GAP;
          }
        }

        function spawnSparkles(x: number, y: number) {
          for (let i = 0; i < SPARKLE_RATE; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 1.8 + 0.4;
            sparkles.push({
              x,
              y,
              vx: Math.cos(angle) * speed,
              vy: Math.sin(angle) * speed,
              life: 1,
              maxLife: Math.random() * 0.6 + 0.4,
              size: Math.random() * 3 + 1.5,
              hue: Math.random() * 60 + 200, // blue-violet-pink range
            });
          }
        }

        p.setup = () => {
          canvasW = canvasRef.current?.offsetWidth ?? 600;
          const cnv = p.createCanvas(canvasW, 60);
          cnv.parent(canvasRef.current!);
          p.textAlign(p.CENTER, p.CENTER);
          buildLetters();
        };

        p.windowResized = () => {
          canvasW = canvasRef.current?.offsetWidth ?? 600;
          p.resizeCanvas(canvasW, 60);
          buildLetters();
        };

        p.draw = () => {
          p.clear();

          // ── update & draw sparkles ────────────────────────────────────────
          sparkles = sparkles.filter((s) => s.life > 0);
          for (const s of sparkles) {
            s.x += s.vx;
            s.y += s.vy;
            s.vy += 0.05; // slight gravity
            s.life -= 1 / (s.maxLife * 60);

            const alpha = p.map(s.life, 0, 1, 0, 220);
            p.noStroke();
            p.fill(s.hue, 80, 95, alpha / 255); // HSB fill – switch mode below
            p.colorMode(p.HSB, 360, 100, 100, 255);
            p.fill(s.hue, 80, 100, alpha);

            // star shape
            p.push();
            p.translate(s.x, s.y);
            p.rotate(p.frameCount * 0.1);
            drawStar(p, 0, 0, s.size * 0.4, s.size, 4);
            p.pop();

            p.colorMode(p.RGB, 255, 255, 255, 255);
          }

          // ── update & draw letters ────────────────────────────────────────
          const t = p.frameCount;
          for (let i = 0; i < letters.length; i++) {
            const l = letters[i];

            // sine-wave bounce
            l.y = l.baseY + Math.sin(t * BOUNCE_SPEED + l.phase) * BOUNCE_AMP;

            // occasional sparkle from top of letter
            if (p.frameCount % 2 === 0 && Math.random() < 0.15) {
              spawnSparkles(l.x, l.y - FONT_SIZE * 0.8);
            }

            // colour: cycle hue slowly through purple/blue/teal
            p.colorMode(p.HSB, 360, 100, 100, 255);
            const hue = (200 + i * 12 + t * 0.4) % 360;
            p.fill(hue, 55, 100, 255);
            p.colorMode(p.RGB, 255, 255, 255, 255);

            p.noStroke();
            p.textSize(l.size);
            p.textFont("monospace");
            p.textStyle(p.BOLD);
            p.text(l.char, l.x, l.y);
          }
        };

        function drawStar(
          pg: InstanceType<typeof P5>,
          x: number,
          y: number,
          r1: number,
          r2: number,
          npoints: number
        ) {
          const angle = (Math.PI * 2) / npoints;
          const half = angle / 2;
          pg.beginShape();
          for (let a = -Math.PI / 2; a < Math.PI * 2 - Math.PI / 2; a += angle) {
            pg.vertex(x + Math.cos(a) * r2, y + Math.sin(a) * r2);
            pg.vertex(
              x + Math.cos(a + half) * r1,
              y + Math.sin(a + half) * r1
            );
          }
          pg.endShape(pg.CLOSE);
        }
      };

      p5Instance = new P5(sketch);
    }

    init();

    return () => {
      p5Instance?.remove();
    };
  }, []);

  return (
    <footer className="relative w-full mt-auto border-t border-border/40 bg-background/80 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-4 py-1">
        {/* p5 canvas sits behind the link row */}
        <div ref={canvasRef} className="w-full" aria-hidden="true" />

        {/* GitHub link — sits below the canvas */}
        <div className="flex items-center justify-center gap-2 pb-3 -mt-1">
          <Link
            href="https://github.com/Github-Emmi/"
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <GitFork className="h-3.5 w-3.5 transition-transform group-hover:scale-110" />
            <span>github.com/Github-Emmi</span>
          </Link>
        </div>
      </div>
    </footer>
  );
}
