/**
 * PulseForge Cinema Viewport — multi-axis armature + viseme + pupil safety
 */
(function (global) {
  const VISEME = {
    A: { jawY: -12.0, scaleX: 1.05, puckerZ: 0.1 },
    E: { jawY: -4.0, scaleX: 1.35, puckerZ: 0.0 },
    O: { jawY: -15.0, scaleX: 0.70, puckerZ: 0.85 },
    U: { jawY: -8.0, scaleX: 0.60, puckerZ: 1.0 },
    REST: { jawY: 0.0, scaleX: 1.0, puckerZ: 0.0 }
  };
  const ALIAS = { AH: "A", EE: "E", EH: "E", OH: "O", OO: "U", A: "A", E: "E", O: "O", U: "U" };

  class PulseForgeCinemaViewport {
    constructor(containerId) {
      this.containerId = containerId;
      this.container = null;
      this.scene = null;
      this.camera = null;
      this.renderer = null;
      this.neckBone = null;
      this.headBone = null;
      this.jawBone = null;
      this.leftEye = null;
      this.rightEye = null;
      this.mouthMesh = null;
      this.minPupilSpacingMm = 8.5;
      this._loopTimer = null;
      this.ready = false;
      this.lookAt = { x: 0, y: 1.75, z: 4 };
    }

    init() {
      this.container = document.getElementById(this.containerId);
      if (!this.container) return false;
      if (typeof THREE === "undefined") {
        this.container.innerHTML =
          '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#8892a8;font-size:0.8rem;padding:8px;text-align:center">Three.js offline — armature preview unavailable</div>';
        return false;
      }

      const w = this.container.clientWidth || 320;
      const h = this.container.clientHeight || 200;

      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(0x0a0c12);

      this.camera = new THREE.PerspectiveCamera(42, w / h, 0.1, 100);
      this.camera.position.set(0, 1.6, 5.5);

      this.renderer = new THREE.WebGLRenderer({ antialias: true });
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      this.renderer.setSize(w, h);
      this.container.innerHTML = "";
      this.container.appendChild(this.renderer.domElement);

      this.scene.add(new THREE.AmbientLight(0xffffff, 0.35));
      const key = new THREE.DirectionalLight(0x7c6cf0, 0.9);
      key.position.set(2, 5, 4);
      this.scene.add(key);

      // Neck → Head hierarchy
      this.neckBone = new THREE.Group();
      this.neckBone.position.set(0, 1.35, 0);
      this.scene.add(this.neckBone);

      this.headBone = new THREE.Group();
      this.headBone.position.set(0, 0.28, 0);
      this.neckBone.add(this.headBone);

      const headMesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.42, 20, 20),
        new THREE.MeshStandardMaterial({ color: 0x16161e, roughness: 0.65, wireframe: true })
      );
      headMesh.scale.set(1, 1.15, 1);
      this.headBone.add(headMesh);

      // Jaw
      this.jawBone = new THREE.Mesh(
        new THREE.BoxGeometry(0.28, 0.1, 0.22),
        new THREE.MeshStandardMaterial({ color: 0x2a3348, roughness: 0.8 })
      );
      this.jawBone.position.set(0, -0.32, 0.22);
      this.headBone.add(this.jawBone);

      // Mouth accent
      this.mouthMesh = new THREE.Mesh(
        new THREE.BoxGeometry(0.2, 0.06, 0.08),
        new THREE.MeshStandardMaterial({
          color: 0x00d2c6,
          emissive: 0x00d2c6,
          emissiveIntensity: 0.3
        })
      );
      this.mouthMesh.position.set(0, -0.28, 0.38);
      this.headBone.add(this.mouthMesh);

      // Pupils
      const pupilMat = new THREE.MeshBasicMaterial({ color: 0x00d2c6 });
      this.leftEye = new THREE.Mesh(new THREE.SphereGeometry(0.045, 10, 10), pupilMat);
      this.leftEye.position.set(-0.14, 0.08, 0.38);
      this.headBone.add(this.leftEye);
      this.rightEye = new THREE.Mesh(new THREE.SphereGeometry(0.045, 10, 10), pupilMat.clone());
      this.rightEye.position.set(0.14, 0.08, 0.38);
      this.headBone.add(this.rightEye);

      // Torso hint
      const torso = new THREE.Mesh(
        new THREE.CylinderGeometry(0.25, 0.35, 0.9, 12),
        new THREE.MeshStandardMaterial({ color: 0x1a2030, wireframe: true })
      );
      torso.position.set(0, 0.7, 0);
      this.scene.add(torso);

      const animate = () => {
        if (!this.renderer) return;
        requestAnimationFrame(animate);
        this.renderer.render(this.scene, this.camera);
      };
      animate();

      window.addEventListener("resize", () => {
        if (!this.container || !this.camera || !this.renderer) return;
        const nw = this.container.clientWidth;
        const nh = this.container.clientHeight;
        this.camera.aspect = nw / Math.max(1, nh);
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(nw, nh);
      });

      this.ready = true;
      this.solveVisemeMechanics("REST");
      this.solveAnatomicalBones(this.lookAt.x, this.lookAt.y, this.lookAt.z);
      return true;
    }

    solveAnatomicalBones(lookX, lookY, lookZ) {
      if (!this.headBone || !this.neckBone) return;
      this.lookAt = { x: lookX, y: lookY, z: lookZ };

      const dx = lookX - 0;
      const dy = lookY - 1.6;
      const dz = lookZ - 0;
      const distXZ = Math.sqrt(dx * dx + dz * dz) || 0.001;

      let neckYaw = Math.atan2(dx, dz) * 0.45;
      let neckPitch = -Math.atan2(dy, distXZ) * 0.45;
      // Clamp ±45° yaw, ±30° pitch
      neckYaw = Math.max(-0.785, Math.min(0.785, neckYaw));
      neckPitch = Math.max(-0.523, Math.min(0.523, neckPitch));

      this.neckBone.rotation.y = neckYaw;
      this.neckBone.rotation.x = neckPitch;

      const eyeYaw = Math.max(-0.4, Math.min(0.4, (Math.atan2(dx, dz) - neckYaw) * 0.5));
      if (this.leftEye) this.leftEye.rotation.y = eyeYaw;
      if (this.rightEye) this.rightEye.rotation.y = eyeYaw;

      return this.verifyPupilClearance();
    }

    verifyPupilClearance() {
      if (!this.leftEye || !this.rightEye || typeof THREE === "undefined") return true;
      const left = new THREE.Vector3();
      const right = new THREE.Vector3();
      this.leftEye.getWorldPosition(left);
      this.rightEye.getWorldPosition(right);
      // Scene units ≈ meters-ish; scale for "mm" guide (×1000 of local eye distance)
      const distanceMm = left.distanceTo(right) * 1000;
      const ok = distanceMm >= this.minPupilSpacingMm;
      if (!ok) {
        console.warn("[Armature] Pupil spacing " + distanceMm.toFixed(2) + "mm < " + this.minPupilSpacingMm);
        const st = document.getElementById("status");
        if (st) {
          st.textContent = "Rig warning: pupil spacing " + distanceMm.toFixed(1) + "mm";
          st.className = "status warn";
        }
      }
      return ok;
    }

    solveVisemeMechanics(visemeKey) {
      const raw = String(visemeKey || "REST").toUpperCase();
      const key = ALIAS[raw] || (VISEME[raw] ? raw : "REST");
      const t = VISEME[key] || VISEME.REST;

      if (this.jawBone) {
        this.jawBone.position.y = -0.32 + t.jawY * 0.008;
        this.jawBone.scale.x = t.scaleX;
      }
      if (this.mouthMesh) {
        this.mouthMesh.scale.set(t.scaleX, Math.max(0.2, 1 + t.jawY / 25), 1 + t.puckerZ * 0.4);
        this.mouthMesh.position.set(0, -0.28 + t.jawY * 0.006, 0.38 + t.puckerZ * 0.05);
      }
      return {
        viseme: key,
        jawY: t.jawY,
        scaleX: t.scaleX,
        puckerZ: t.puckerZ,
        jaw_translation_y_mm: t.jawY,
        mouth_scale_x: t.scaleX,
        lip_pucker_z_factor: t.puckerZ
      };
    }

    animateVocalPerformanceLoop(syllables, stepMs) {
      if (this._loopTimer) clearInterval(this._loopTimer);
      let i = 0;
      const arr = syllables && syllables.length ? syllables : ["REST"];
      this._loopTimer = setInterval(() => {
        if (i >= arr.length) {
          this.solveVisemeMechanics("REST");
          clearInterval(this._loopTimer);
          this._loopTimer = null;
          return;
        }
        this.solveVisemeMechanics(arr[i]);
        i++;
      }, Math.max(80, stepMs || 320));
    }

    stopLoop() {
      if (this._loopTimer) {
        clearInterval(this._loopTimer);
        this._loopTimer = null;
      }
      this.solveVisemeMechanics("REST");
    }
  }

  // Export class for external prototype extensions / tests
  global.PulseForgeCinemaViewport = PulseForgeCinemaViewport;
  global.VISEME_TABLE = VISEME;

  /** Spectral-flux onset → bounded look-at nudge (clamps pupil spacing). */
  PulseForgeCinemaViewport.prototype.registerTransientLookAtNudge = function (spectralFlux) {
    const flux = Math.max(0, Math.min(10, parseFloat(spectralFlux) || 0));
    if (flux < 2.5) return;
    const base = this.lookAt || { x: 0, y: 1.75, z: 4 };
    const nx = base.x + Math.sin(flux * 1.7) * 0.35;
    const ny = base.y + Math.cos(flux * 0.9) * 0.12;
    const nz = base.z;
    this.solveAnatomicalBones(nx, ny, nz);
  };

  global.pulseForgeCinemaSync = new PulseForgeCinemaViewport("canvas-viseme-viewport");
  try { global.pulseForgeCinemaSync.init(); } catch (e) { console.warn("[Cinema] init deferred", e); }
})(window);
