import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(
  22,
  innerWidth / innerHeight,
  0.01,
  100,
);
camera.position.set(0, 1.35, 4.2);

const renderer = new THREE.WebGLRenderer({
  alpha: true,
  antialias: true,
  powerPreference: 'high-performance',
});
renderer.setClearColor(0x000000, 0);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.domElement.style.visibility = 'visible';
document.getElementById('app').appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xffffff, 0x666666, 2.3));
const key = new THREE.DirectionalLight(0xffffff, 2.2);
key.position.set(1.5, 2.5, 3);
scene.add(key);

let vrm = null;
let currentExpression = 'neutral';
let speaking = false;
let mouthPhase = 0;
let nextBlinkAt = performance.now() + 2500;
let avatarBaseX = 0;
let avatarBaseY = 0;
let lastFit = null;
let behavior = {
  spontaneousGestures: true,
  gestureMinSeconds: 12,
  gestureMaxSeconds: 30,
};
let activeGesture = null;
let nextGestureAt = performance.now() + 15000;
const modelCenter = new THREE.Vector3(0, 1, 0);
const modelSize = new THREE.Vector3(1, 2, 1);
const lookTarget = new THREE.Object3D();
lookTarget.position.set(0, 1.45, 2.5);
scene.add(lookTarget);

const idleBones = new Map();
const tmpEuler = new THREE.Euler();
const tmpQuat = new THREE.Quaternion();

function setFatalError(value) {
  const message = value instanceof Error
    ? (value.stack || value.message)
    : String(value ?? 'unknown renderer error');
  console.error('[avatar-fatal]', message);
  document.body.dataset.error = message;
}

window.addEventListener('error', event => {
  setFatalError(event.error || event.message);
});

window.addEventListener('unhandledrejection', event => {
  setFatalError(event.reason);
});

renderer.domElement.addEventListener('webglcontextlost', event => {
  event.preventDefault();
  console.warn('[avatar-webgl] context lost');
  document.body.dataset.webglLost = 'true';
});

renderer.domElement.addEventListener('webglcontextrestored', () => {
  console.info('[avatar-webgl] context restored');
  document.body.dataset.webglLost = '';
  fitCamera();
});

function setOnlyExpression(name, weight = 1) {
  if (!vrm?.expressionManager) return;
  const manager = vrm.expressionManager;
  for (const expression of [
    'happy',
    'angry',
    'sad',
    'relaxed',
    'surprised',
  ]) {
    manager.setValue(expression, 0);
  }
  if (name && name !== 'neutral') manager.setValue(name, weight);
  currentExpression = name || 'neutral';
}

function captureBone(name) {
  const node = vrm?.humanoid?.getNormalizedBoneNode(name);
  if (!node) return;
  idleBones.set(name, {
    node,
    baseQuaternion: node.quaternion.clone(),
  });
}

function rotateBone(name, x = 0, y = 0, z = 0) {
  const item = idleBones.get(name);
  if (!item) return;
  tmpEuler.set(x, y, z, 'XYZ');
  tmpQuat.setFromEuler(tmpEuler);
  item.node.quaternion.copy(item.baseQuaternion).multiply(tmpQuat);
}

function setupIdleRig() {
  for (const name of [
    'hips',
    'spine',
    'chest',
    'upperChest',
    'neck',
    'head',
    'leftShoulder',
    'rightShoulder',
    'leftUpperArm',
    'rightUpperArm',
    'leftLowerArm',
    'rightLowerArm',
    'leftHand',
    'rightHand',
    'leftUpperLeg',
    'rightUpperLeg',
    'leftLowerLeg',
    'rightLowerLeg',
  ]) {
    captureBone(name);
  }

  // Apply one frame before calculating the bounding box so the full-body fit
  // reflects the relaxed pose instead of the source T-pose.
  applyIdlePose(0);
  vrm.update(0);
}


function randomGestureDelayMs() {
  const min = Math.max(3, Number(behavior.gestureMinSeconds) || 12);
  const max = Math.max(min, Number(behavior.gestureMaxSeconds) || 30);
  return (min + Math.random() * (max - min)) * 1000;
}

function scheduleNextGesture(now = performance.now()) {
  nextGestureAt = now + randomGestureDelayMs();
}

function startGesture(name = 'auto', now = performance.now()) {
  if (!vrm) return;

  const choices = [
    'hairTouch',
    'hop',
    'dance',
    'wave',
    'stretch',
    'ponder',
  ];
  const selected = name === 'auto'
    ? choices[Math.floor(Math.random() * choices.length)]
    : name;

  const durations = {
    lookAround: 4.2,
    stretch: 3.8,
    wave: 3.4,
    ponder: 4.6,
    hairTouch: 3.8,
    hop: 2.4,
    dance: 5.4,
  };

  activeGesture = {
    name: choices.includes(selected) ? selected : 'lookAround',
    startedAt: now * 0.001,
    duration: durations[selected] ?? 4.0,
  };
  console.info('[avatar-gesture]', activeGesture.name);
}

function gesturePose(t) {
  const result = {
    leftUpperZ: 0,
    rightUpperZ: 0,
    leftLowerZ: 0,
    rightLowerZ: 0,
    leftLowerX: 0,
    rightLowerX: 0,
    headX: 0,
    headY: 0,
    headZ: 0,
    neckY: 0,
    chestX: 0,
    chestY: 0,
    chestZ: 0,
    leftShoulderZ: 0,
    rightShoulderZ: 0,
    leftUpperLegX: 0,
    rightUpperLegX: 0,
    leftLowerLegX: 0,
    rightLowerLegX: 0,
    hipsY: 0,
    hipsZ: 0,
    rootX: 0,
    rootY: 0,
  };

  if (!activeGesture) return result;

  const p = (t - activeGesture.startedAt) / activeGesture.duration;
  if (p >= 1) {
    activeGesture = null;
    scheduleNextGesture();
    return result;
  }

  const clamped = Math.max(0, Math.min(1, p));
  const envelope = Math.sin(Math.PI * clamped);
  const wave = Math.sin(clamped * Math.PI * 6);

  if (activeGesture.name === 'lookAround') {
    result.headY = envelope * 0.22 * Math.sin(clamped * Math.PI * 2);
    result.neckY = envelope * 0.08 * Math.sin(clamped * Math.PI * 2);
    result.headZ = envelope * 0.025;
  } else if (activeGesture.name === 'stretch') {
    result.leftUpperZ = envelope * 0.72;
    result.rightUpperZ = -envelope * 0.72;
    result.leftLowerZ = envelope * 0.10;
    result.rightLowerZ = -envelope * 0.10;
    result.chestX = -envelope * 0.035;
    result.headX = envelope * 0.025;
  } else if (activeGesture.name === 'wave') {
    result.rightUpperZ = -envelope * 0.70;
    result.rightLowerX = envelope * 0.55;
    result.rightLowerZ = envelope * (0.30 + wave * 0.16);
    result.headY = -envelope * 0.08;
  } else if (activeGesture.name === 'ponder') {
    result.leftUpperZ = envelope * 0.22;
    result.leftLowerX = -envelope * 0.46;
    result.leftLowerZ = -envelope * 0.20;
    result.headY = envelope * 0.10;
    result.headZ = -envelope * 0.035;
    result.chestY = -envelope * 0.035;
  } else if (activeGesture.name === 'hairTouch') {
    // Raise one hand toward the side of the head, hold briefly, then return.
    const hold = Math.sin(Math.PI * Math.min(1, clamped * 1.12));
    result.rightUpperZ = -hold * 0.92;
    result.rightLowerX = hold * 0.92;
    result.rightLowerZ = hold * 0.38;
    result.rightShoulderZ = -hold * 0.10;
    result.headY = hold * 0.055;
    result.headZ = -hold * 0.055;
    result.chestY = -hold * 0.025;
  } else if (activeGesture.name === 'hop') {
    // A small whole-body hop with a soft knee bend and arm reaction.
    const hop = Math.pow(Math.sin(Math.PI * clamped), 2);
    const crouch = Math.sin(Math.PI * clamped) * (1 - hop);
    result.rootY = hop * Math.max(0.035, modelSize.y * 0.035);
    result.leftUpperLegX = -crouch * 0.12;
    result.rightUpperLegX = -crouch * 0.12;
    result.leftLowerLegX = crouch * 0.20;
    result.rightLowerLegX = crouch * 0.20;
    result.leftUpperZ = envelope * 0.16;
    result.rightUpperZ = -envelope * 0.16;
    result.chestX = -envelope * 0.025;
  } else if (activeGesture.name === 'dance') {
    // Short two-beat sway: hips, shoulders and arms move together so the
    // action reads as a tiny dance rather than generic idle noise.
    const phase = clamped * Math.PI * 4;
    const sway = Math.sin(phase) * envelope;
    const beat = Math.sin(phase * 2) * envelope;
    result.hipsZ = sway * 0.075;
    result.hipsY = sway * 0.035;
    result.chestZ = -sway * 0.055;
    result.headZ = sway * 0.035;
    result.leftUpperZ = envelope * (0.18 + 0.12 * beat);
    result.rightUpperZ = -envelope * (0.18 - 0.12 * beat);
    result.leftLowerZ = -beat * 0.10;
    result.rightLowerZ = beat * 0.10;
    result.rootX = sway * Math.max(0.01, modelSize.x * 0.025);
    result.rootY = Math.abs(beat) * Math.max(0.004, modelSize.y * 0.006);
  }

  return result;
}

function applyIdlePose(t) {
  if (!vrm) return;

  const breath = Math.sin(t * 1.8);
  const slow = Math.sin(t * 0.72);
  const slow2 = Math.sin(t * 0.47 + 1.3);
  const talkEnergy = speaking ? 1 : 0;
  const moodEnergy =
    currentExpression === 'happy' ? 0.7
      : currentExpression === 'angry' ? 0.35
        : currentExpression === 'surprised' ? 0.8
          : 0;
  const gesture = gesturePose(t);

  // Source VRM arrives close to a T-pose. Rotate the upper arms down into a
  // relaxed standing pose. The small oscillations make the shoulders and
  // hands feel alive without looking like a looping dance.
  rotateBone(
    'leftUpperArm',
    0.035 + breath * 0.008,
    -0.025,
    -1.30 + slow * 0.025 - talkEnergy * 0.035 + gesture.leftUpperZ,
  );
  rotateBone(
    'rightUpperArm',
    0.035 - breath * 0.008,
    0.025,
    1.30 - slow * 0.025 + talkEnergy * 0.035 + gesture.rightUpperZ,
  );

  rotateBone(
    'leftLowerArm',
    -0.08 + talkEnergy * 0.035 + gesture.leftLowerX,
    0.02,
    -0.10 + slow2 * 0.018 + gesture.leftLowerZ,
  );
  rotateBone(
    'rightLowerArm',
    -0.08 + talkEnergy * 0.035 + gesture.rightLowerX,
    -0.02,
    0.10 - slow2 * 0.018 + gesture.rightLowerZ,
  );

  rotateBone(
    'leftHand',
    0.02 + breath * 0.01,
    0,
    -0.035 + slow * 0.012,
  );
  rotateBone(
    'rightHand',
    0.02 - breath * 0.01,
    0,
    0.035 - slow * 0.012,
  );

  rotateBone(
    'hips',
    0,
    slow * 0.008 + gesture.hipsY,
    slow2 * 0.014 + gesture.hipsZ,
  );
  rotateBone('leftUpperLeg', gesture.leftUpperLegX, 0, 0);
  rotateBone('rightUpperLeg', gesture.rightUpperLegX, 0, 0);
  rotateBone('leftLowerLeg', gesture.leftLowerLegX, 0, 0);
  rotateBone('rightLowerLeg', gesture.rightLowerLegX, 0, 0);
  rotateBone('spine', breath * 0.006, 0, -slow2 * 0.006);
  rotateBone('leftShoulder', 0, 0, gesture.leftShoulderZ);
  rotateBone('rightShoulder', 0, 0, gesture.rightShoulderZ);
  rotateBone(
    'chest',
    0.014 + breath * 0.012 + talkEnergy * 0.006 + gesture.chestX,
    slow * 0.006 + gesture.chestY,
    slow2 * 0.009 + gesture.chestZ,
  );
  rotateBone(
    'upperChest',
    breath * 0.008,
    -slow * 0.006,
    -slow2 * 0.006,
  );
  rotateBone(
    'neck',
    -0.01 + breath * 0.004,
    slow * 0.014 + gesture.neckY,
    slow2 * 0.008,
  );
  rotateBone(
    'head',
    breath * 0.004 + gesture.headX,
    slow * 0.012 + gesture.headY,
    slow2 * (0.010 + moodEnergy * 0.004) + gesture.headZ,
  );

  const bodyScale = Math.max(1, modelSize.y);
  vrm.scene.position.x =
    avatarBaseX
    + slow * Math.max(0.003, modelSize.x * 0.008)
    + gesture.rootX;
  vrm.scene.position.y =
    avatarBaseY
    + breath * bodyScale * 0.0035
    + gesture.rootY;
}

function fitCamera() {
  if (!vrm) return;

  vrm.scene.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(vrm.scene);
  if (box.isEmpty()) {
    setFatalError('VRM bounding box is empty');
    return;
  }

  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const aspect = Math.max(0.1, innerWidth / Math.max(1, innerHeight));
  const verticalFov = THREE.MathUtils.degToRad(camera.fov);
  const tanHalf = Math.tan(verticalFov / 2);

  const distanceForHeight = size.y / 2 / tanHalf;
  const distanceForWidth = size.x / 2 / (aspect * tanHalf);
  const margin = 0.18;
  const distance =
    Math.max(distanceForHeight, distanceForWidth) * (1 + margin)
    + Math.max(0.02, size.z * 0.5);

  camera.aspect = aspect;
  camera.near = 0.01;
  camera.far = Math.max(30, distance + size.y * 3 + size.z * 2);
  camera.position.set(center.x, center.y, center.z + distance);
  camera.lookAt(center);
  camera.updateProjectionMatrix();

  modelCenter.copy(center);
  modelSize.copy(size);
  lastFit = {
    viewport: [innerWidth, innerHeight],
    aspect,
    bounds: {
      min: box.min.toArray(),
      max: box.max.toArray(),
      size: size.toArray(),
      center: center.toArray(),
    },
    camera: {
      fov: camera.fov,
      position: camera.position.toArray(),
      near: camera.near,
      far: camera.far,
      distance,
      margin,
    },
  };

  console.info('[avatar-fit]', JSON.stringify(lastFit));
}

window.companionAvatar = {
  setExpression(name, weight = 1) {
    setOnlyExpression(name, weight);
  },
  setSpeaking(value) {
    speaking = !!value;
  },
  configureBehavior(options = {}) {
    behavior = {
      ...behavior,
      ...options,
    };
    scheduleNextGesture();
    console.info('[avatar-behavior]', JSON.stringify(behavior));
  },
  playGesture(name = 'auto') {
    startGesture(String(name || 'auto'));
  },
  setLook(x, y) {
    const dx = Number(x);
    const dy = Number(y);
    lookTarget.position.set(
      modelCenter.x + dx * Math.max(0.25, modelSize.x * 0.8),
      modelCenter.y + dy * Math.max(0.3, modelSize.y * 0.35),
      modelCenter.z + Math.max(2.0, modelSize.y * 1.6),
    );
    if (vrm?.lookAt) vrm.lookAt.target = lookTarget;
  },
  isReady() {
    return !!vrm;
  },
  diagnostics() {
    return {
      ready: !!vrm,
      expression: currentExpression,
      fit: lastFit,
      webglLost: document.body.dataset.webglLost || '',
      error: document.body.dataset.error || '',
      userAgent: navigator.userAgent,
      webgl: renderer.capabilities?.isWebGL2 ? 'WebGL2' : 'WebGL1',
      behavior,
      activeGesture: activeGesture?.name || '',
    };
  },
};

const loader = new GLTFLoader();
loader.register(parser => new VRMLoaderPlugin(parser));
loader.load(
  '/model.vrm',
  gltf => {
    try {
      vrm = gltf.userData.vrm;
      if (!vrm) {
        throw new Error('VRMLoaderPlugin did not return a VRM instance');
      }

      VRMUtils.removeUnnecessaryVertices(gltf.scene);
      VRMUtils.combineSkeletons(gltf.scene);
      VRMUtils.combineMorphs(vrm);
      VRMUtils.rotateVRM0(vrm);

      vrm.scene.traverse(obj => {
        obj.frustumCulled = false;
      });
      scene.add(vrm.scene);

      avatarBaseX = vrm.scene.position.x;
      avatarBaseY = vrm.scene.position.y;

      setupIdleRig();
      scheduleNextGesture();

      if (vrm.lookAt) vrm.lookAt.target = lookTarget;

      setOnlyExpression('neutral');
      fitCamera();

      document.body.dataset.ready = 'true';
      console.info('[avatar-ready]', JSON.stringify({
        name: vrm.meta?.name || '',
        expressions: Object.keys(
          vrm.expressionManager?.expressionMap || {},
        ),
        idleBones: [...idleBones.keys()],
      }));
    } catch (error) {
      setFatalError(error);
    }
  },
  progress => {
    if (progress?.total) {
      const percent = Math.round((progress.loaded / progress.total) * 100);
      if ([25, 50, 75, 100].includes(percent)) {
        console.info('[avatar-load]', percent + '%');
      }
    }
  },
  error => {
    setFatalError(error);
  },
);

const clock = new THREE.Clock();
function animate(now) {
  requestAnimationFrame(animate);
  const dt = clock.getDelta();

  if (vrm) {
    if (
      behavior.spontaneousGestures
      && !speaking
      && !activeGesture
      && now >= nextGestureAt
    ) {
      startGesture('auto', now);
    }

    const manager = vrm.expressionManager;
    if (manager) {
      if (now >= nextBlinkAt) {
        manager.setValue('blink', 1);
        setTimeout(() => {
          if (vrm?.expressionManager) {
            vrm.expressionManager.setValue('blink', 0);
          }
        }, 115);
        nextBlinkAt = now + 2200 + Math.random() * 3400;
      }

      for (const viseme of ['aa', 'ih', 'ou', 'ee', 'oh']) {
        manager.setValue(viseme, 0);
      }
      if (speaking) {
        mouthPhase += dt * 9;
        const weight = 0.25 + 0.65 * Math.abs(Math.sin(mouthPhase));
        const sequence = ['aa', 'ih', 'ou', 'ee', 'oh'];
        manager.setValue(
          sequence[Math.floor(mouthPhase) % sequence.length],
          weight,
        );
      }
    }

    applyIdlePose(now * 0.001);
    vrm.update(dt);
  }

  renderer.render(scene, camera);
}
requestAnimationFrame(animate);

addEventListener('resize', () => {
  renderer.setSize(innerWidth, innerHeight);
  fitCamera();
});
