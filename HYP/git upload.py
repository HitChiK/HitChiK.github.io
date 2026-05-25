"""
GitHub 폴더 업로드 스크립트
소스: C:\\Users\\apple\\Desktop\\캐릭터 이미지 모음\\업로드용 폴더
대상: github.com/HitChiK/HitChiK.github.io  →  HYP/
"""

import subprocess
import shutil
import tempfile
import sys
from pathlib import Path

# ========== 설정 ==========
SOURCE_DIR     = r"C:\Users\apple\Desktop\캐릭터 이미지 모음\업로드용 폴더"
REPO_URL       = "https://github.com/HitChiK/HitChiK.github.io.git"
TARGET_SUBPATH = "HYP"
BRANCH         = "main"
COMMIT_MESSAGE = "Upload HYP character images"
LARGE_FILE_MB  = 50          # 경고 임계값 (GitHub 제한 100MB)
# =========================

# 작업 폴더는 시스템 TEMP에 생성 → 소스와 절대 분리
WORK_DIR = Path(tempfile.gettempdir()) / "_hyp_repo_work"


def run(cmd, cwd=None):
    """git 명령 실행. 실패 시 stderr 출력 후 중단."""
    result = subprocess.run(
        cmd, cwd=cwd, shell=False,
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        print("─" * 50)
        print(f"❌ 명령 실패: {' '.join(cmd)}")
        if result.stdout: print("STDOUT:", result.stdout)
        if result.stderr: print("STDERR:", result.stderr)
        print("─" * 50)
        sys.exit(1)
    return result.stdout


def check_environment(src: Path):
    """실행 전 환경 점검."""
    # 1) 소스 폴더 존재 확인
    if not src.is_dir():
        print(f"❌ 소스 폴더가 없습니다: {src}")
        sys.exit(1)

    # 2) 소스 폴더가 비어있지 않은지
    items = list(src.iterdir())
    if not items:
        print(f"❌ 소스 폴더가 비어있습니다: {src}")
        sys.exit(1)

    # 3) 작업 폴더가 소스 내부에 있지 않은지 (안전장치)
    try:
        WORK_DIR.resolve().relative_to(src.resolve())
        print(f"❌ 작업 폴더({WORK_DIR})가 소스 폴더 내부에 있습니다. 중단.")
        sys.exit(1)
    except ValueError:
        pass  # 정상

    # 4) Git 설치 확인
    if shutil.which("git") is None:
        print("❌ Git이 설치돼 있지 않거나 PATH에 없습니다.")
        sys.exit(1)

    # 5) 대용량 파일 검사
    large_files = []
    total_size = 0
    file_count = 0
    for f in src.rglob("*"):
        if f.is_file():
            size = f.stat().st_size
            total_size += size
            file_count += 1
            if size > LARGE_FILE_MB * 1024 * 1024:
                large_files.append((f, size))

    print(f"📊 파일 {file_count}개, 총 {total_size / 1024 / 1024:.1f} MB")

    if large_files:
        print(f"\n⚠️  {LARGE_FILE_MB}MB 초과 파일 발견:")
        for f, s in large_files:
            print(f"   - {f.name}: {s / 1024 / 1024:.1f} MB")
        print(f"   (GitHub은 100MB 초과 시 push를 거부합니다)")
        ans = input("\n계속 진행하시겠습니까? [y/N]: ").strip().lower()
        if ans != "y":
            print("중단됨.")
            sys.exit(0)


def main():
    src = Path(SOURCE_DIR).resolve()

    print("=" * 50)
    print("GitHub 폴더 업로드")
    print("=" * 50)
    print(f"소스: {src}")
    print(f"대상: {REPO_URL} → {TARGET_SUBPATH}/")
    print(f"작업: {WORK_DIR}")
    print("=" * 50)

    check_environment(src)

    # 실행 확인
    ans = input("\n진행하시겠습니까? [y/N]: ").strip().lower()
    if ans != "y":
        print("중단됨.")
        sys.exit(0)

    # 이전 작업 폴더 정리
    if WORK_DIR.exists():
        print(f"\n기존 작업 폴더 정리 중...")
        shutil.rmtree(WORK_DIR, ignore_errors=True)

    try:
        # 1) Clone
        print(f"\n[1/4] Cloning {REPO_URL} ...")
        run(["git", "clone", "--depth", "1", "--branch", BRANCH,
             REPO_URL, str(WORK_DIR)])

        # 2) 파일 복사
        print(f"\n[2/4] Copying files to {TARGET_SUBPATH}/ ...")
        dst = WORK_DIR / TARGET_SUBPATH
        dst.mkdir(parents=True, exist_ok=True)

        for item in src.iterdir():
            target = dst / item.name
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)
                print(f"   + [DIR]  {item.name}")
            else:
                shutil.copy2(item, target)
                print(f"   + [FILE] {item.name}")

        # 3) Commit
        print(f"\n[3/4] Committing ...")
        run(["git", "add", "."], cwd=WORK_DIR)

        status = run(["git", "status", "--porcelain"], cwd=WORK_DIR)
        if not status.strip():
            print("   변경사항 없음. push 생략.")
            return

        run(["git", "commit", "-m", COMMIT_MESSAGE], cwd=WORK_DIR)

        # 4) Push
        print(f"\n[4/4] Pushing to {BRANCH} ...")
        run(["git", "push", "origin", BRANCH], cwd=WORK_DIR)

        print("\n" + "=" * 50)
        print("✅ 업로드 완료")
        print(f"   확인: https://github.com/HitChiK/HitChiK.github.io/tree/{BRANCH}/{TARGET_SUBPATH}")
        print("=" * 50)

    finally:
        # 성공/실패 상관없이 작업 폴더 정리
        if WORK_DIR.exists():
            shutil.rmtree(WORK_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()