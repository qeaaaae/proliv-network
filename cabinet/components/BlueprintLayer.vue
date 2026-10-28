<template>
  <div class="blueprint" aria-hidden="true">
    <div class="drawing drawing--tower">
      <svg viewBox="0 0 220 380">
        <path d="M60 350 95 40M150 350 115 40M40 350H170" />
        <path d="M60 350 144.4 300 71.3 250 133.1 200 82.6 150 121.8 100 92.7 60M150 350 65.6 300 138.7 250 76.9 200 127.4 150 88.2 100 117.3 60" />
        <path d="M65.6 300H144.4M71.3 250H138.7M76.9 200H133.1M82.6 150H127.4M88.2 100H121.8M92.7 60H117.3" />
        <path d="M105 40V6M101 6H109" />
        <rect x="70" y="46" width="11" height="36" rx="2" />
        <rect x="129" y="46" width="11" height="36" rx="2" />
        <rect x="99.5" y="16" width="11" height="30" rx="2" />
        <path class="arc" d="M160 38a32 32 0 0 1 0 52M172 26a50 50 0 0 1 0 76M184 14a68 68 0 0 1 0 100" />
        <path class="arc" d="M50 38a32 32 0 0 0 0 52M38 26a50 50 0 0 0 0 76M26 14a68 68 0 0 0 0 100" />
        <rect x="160" y="316" width="40" height="34" rx="3" />
        <path d="M166 326H194M166 334H194M166 342H184" />
        <path class="dash" d="M105 350V372M20 372H200" />
      </svg>
    </div>

    <div class="drawing drawing--rack">
      <svg viewBox="0 0 250 236">
        <g v-for="unit in 4" :key="unit" :transform="`translate(0 ${(unit - 1) * 54})`">
          <rect x="12" y="10" width="226" height="44" rx="5" />
          <rect x="24" y="20" width="34" height="24" rx="2" />
          <rect x="64" y="20" width="34" height="24" rx="2" />
          <rect x="104" y="20" width="34" height="24" rx="2" />
          <path d="M150 22V42M156 22V42M162 22V42M168 22V42M174 22V42M180 22V42" />
          <circle cx="204" cy="26" r="3" />
          <circle cx="216" cy="26" r="3" />
          <path d="M198 38H224" />
        </g>
        <path class="dash" d="M4 4V232M246 4V232" />
      </svg>
    </div>

    <div class="drawing drawing--phone">
      <svg viewBox="0 0 150 280">
        <rect x="12" y="8" width="126" height="264" rx="22" />
        <rect x="22" y="26" width="106" height="222" rx="10" />
        <path d="M62 16H88" />
        <path d="M32 40V46M38 37V46M44 34V46M50 31V46" />
        <circle cx="75" cy="118" r="34" />
        <circle class="dash" cx="75" cy="118" r="48" />
        <path d="M66 104V132M66 104H80C88 104 92 108 92 113S88 122 80 122H66M80 122 90 132" />
        <path d="M36 186H114M36 200H96M36 214H104" />
        <path d="M60 258H90" />
      </svg>
    </div>

    <div class="drawing drawing--router">
      <svg viewBox="0 0 280 160">
        <path d="M58 86 46 12M140 86V6M222 86 234 12" />
        <circle cx="46" cy="10" r="4" />
        <circle cx="140" cy="4" r="4" />
        <circle cx="234" cy="10" r="4" />
        <rect x="20" y="86" width="240" height="50" rx="12" />
        <circle cx="54" cy="111" r="3.4" />
        <circle cx="70" cy="111" r="3.4" />
        <circle cx="86" cy="111" r="3.4" />
        <circle cx="102" cy="111" r="3.4" />
        <path d="M150 104V118M160 104V118M170 104V118M180 104V118M190 104V118M200 104V118M210 104V118M220 104V118M230 104V118" />
        <path d="M40 136V146M240 136V146" />
        <path class="arc" d="M120 40a28 28 0 0 1 40 0M110 28a44 44 0 0 1 60 0" />
      </svg>
    </div>

    <div class="drawing drawing--laptop">
      <svg viewBox="0 0 320 210">
        <rect x="56" y="8" width="208" height="138" rx="9" />
        <rect x="68" y="20" width="184" height="114" rx="4" />
        <path d="M20 156H300L284 184H36Z" />
        <path d="M58 164H262M64 172H256" />
        <path d="M136 178H184" />
        <path class="dash" d="M92 44H228M92 58H200M92 72H214" />
        <rect x="92" y="88" width="56" height="30" rx="4" />
      </svg>
    </div>

    <div class="drawing drawing--globe">
      <svg viewBox="0 0 220 220">
        <circle cx="110" cy="110" r="88" />
        <ellipse cx="110" cy="110" rx="34" ry="88" />
        <ellipse cx="110" cy="110" rx="64" ry="88" />
        <path d="M22 110H198M34 66H186M34 154H186" />
        <ellipse class="dash" cx="110" cy="110" rx="106" ry="36" transform="rotate(-22 110 110)" />
        <circle cx="196" cy="74" r="5" />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.blueprint {
  position: fixed;
  z-index: var(--layer-blueprint);
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  contain: strict;
}

.drawing {
  position: absolute;
  opacity: var(--opacity, .075);
  animation: blueprint-parallax linear both;
  animation-timeline: scroll(root);
}

.drawing svg {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
  animation: drift var(--drift-time, 26s) var(--ease) infinite;
  fill: none;
  stroke: #fff;
  stroke-width: 1.3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.drawing .dash {
  stroke-dasharray: 2 7;
}

.drawing .arc {
  animation: signal-blink 3.4s var(--ease) infinite;
}

.drawing--tower {
  --tilt: -8deg;
  --opacity: .09;
  --parallax: -120px;
  top: 6vh;
  left: max(-60px, calc(50% - 860px));
  width: clamp(200px, 20vw, 320px);
}

.drawing--rack {
  --tilt: 12deg;
  --drift-time: 31s;
  --parallax: -220px;
  top: 18vh;
  right: max(-70px, calc(50% - 900px));
  width: clamp(220px, 21vw, 330px);
}

.drawing--phone {
  --tilt: 16deg;
  --drift-time: 24s;
  --opacity: .085;
  --parallax: -300px;
  top: 64vh;
  left: max(-30px, calc(50% - 820px));
  width: clamp(110px, 10vw, 170px);
}

.drawing--router {
  --tilt: -9deg;
  --drift-time: 29s;
  --parallax: -180px;
  bottom: 6vh;
  right: max(-40px, calc(50% - 840px));
  width: clamp(220px, 19vw, 300px);
}

.drawing--laptop {
  --tilt: 6deg;
  --drift-time: 34s;
  --opacity: .06;
  --parallax: -360px;
  top: 108vh;
  right: max(-80px, calc(50% - 760px));
  width: clamp(240px, 22vw, 360px);
}

.drawing--globe {
  --tilt: -14deg;
  --drift-time: 27s;
  --opacity: .07;
  --parallax: -420px;
  top: 116vh;
  left: max(-60px, calc(50% - 780px));
  width: clamp(180px, 16vw, 260px);
}

@keyframes blueprint-parallax {
  to {
    transform: translateY(var(--parallax, -160px));
  }
}

@media (max-width: 900px) {
  .drawing {
    --opacity: .05;
  }

  .drawing--laptop,
  .drawing--globe {
    display: none;
  }
}
</style>
