import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(22, innerWidth / innerHeight, 0.01, 100);
camera.position.set(0, 1.35, 4.2);

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setClearColor(0x000000, 0);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
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
let avatarBaseY = 0;
let chestBone = null;
let lastFit = null;
const modelCenter = new THREE.Vector3(0, 1, 0);
const modelSize = new THREE.Vector3(1, 2, 1);
const lookTarget = new THREE.Object3D();
lookTarget.position.set(0, 1.45, 2.5);
scene.add(lookTarget);

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
  setFatalError('WebGL context lost');
});

renderer.domElement.addEventListener('webglcontextrestored', () => {
  console.info('[avatar-webgl] context restored');
});

function setOnlyExpression(name, weight = 1) {
  if (!vrm?.expressionManager) return;
  const manager = vrm.expressionManager;
  for (const expression of ['happy', 'angry', 'sad', 'relaxed', 'surprised']) {
    manager.setValue(expression, 0);
  }
  if (name && name !== 'neutral') manager.setValue(name, weight);
  currentExpression = name || 'neutral';
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
  const margin = 0.16;
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
      error: document.body.dataset.error || '',
      userAgent: navigator.userAgent,
      webgl: renderer.capabilities?.isWebGL2 ? 'WebGL2' : 'WebGL1',
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

      avatarBaseY = vrm.scene.position.y;
      chestBone =
        vrm.humanoid?.getNormalizedBoneNode('upperChest')
        ?? vrm.humanoid?.getNormalizedBoneNode('chest')
        ?? null;

      if (vrm.lookAt) vrm.lookAt.target = lookTarget;

      setOnlyExpression('neutral');
      fitCamera();

      document.body.dataset.ready = 'true';
      console.info('[avatar-ready]', JSON.stringify({
        name: vrm.meta?.name || '',
        specVersion: vrm.meta?.metaVersion || 'VRM1',
        expressions: Object.keys(vrm.expressionManager?.expressionMap || {}),
      }));
    } catch (error) {
      setFatalError(error);
    }
  },
  progress => {
    if (progress?.total) {
      const percent = Math.round((progress.loaded / progress.total) * 100);
      if (percent === 25 || percent === 50 || percent === 75 || percent === 100) {
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
    const manager = vrm.expressionManager;
    if (manager) {
      if (now >= nextBlinkAt) {
        manager.setValue('blink', 1);
        setTimeout(() => {
          if (vrm?.expressionManager) {
            vrm.expressionManager.setValue('blink', 0);
          }
        }, 110);
        nextBlinkAt = now + 2500 + Math.random() * 3500;
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

    const t = now * 0.001;
    vrm.scene.position.y = avatarBaseY + Math.sin(t * 1.7) * 0.004;
    if (chestBone) {
      chestBone.rotation.x = Math.sin(t * 1.7) * 0.008;
      chestBone.rotation.z = Math.sin(t * 0.65) * 0.004;
    }
    vrm.update(dt);
  }

  renderer.render(scene, camera);
}
requestAnimationFrame(animate);

addEventListener('resize', () => {
  renderer.setSize(innerWidth, innerHeight);
  fitCamera();
});
