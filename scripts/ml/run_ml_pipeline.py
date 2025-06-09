#!/usr/bin/env python3
"""
ML 비즈니스 로직 실행 스크립트 (Python 버전)
파일 위치: /mnt/c/dev/movie-mlops/scripts/ml/run_ml_pipeline.py
"""

import subprocess
import sys
import os
import argparse
import time
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

class MLPipelineRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.target_container = None
        
    def print_banner(self):
        print(f"{Colors.PURPLE}{'='*60}{Colors.NC}")
        print(f"{Colors.PURPLE}   🎬 Movie-MLOps ML 파이프라인 실행기 (Python){Colors.NC}")
        print(f"{Colors.PURPLE}   PyTorch 기반 영화 추천 모델 훈련 및 평가{Colors.NC}")
        print(f"{Colors.PURPLE}{'='*60}{Colors.NC}")
        
    def check_container_status(self, container_name):
        """컨테이너 실행 상태 확인"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}"],
                capture_output=True, text=True, check=True
            )
            if container_name in result.stdout.split('\n'):
                print(f"{Colors.GREEN}✅ {container_name} 실행 중{Colors.NC}")
                return True
            else:
                print(f"{Colors.RED}❌ {container_name} 실행되지 않음{Colors.NC}")
                return False
        except subprocess.CalledProcessError:
            return False
            
    def check_pytorch_installation(self, container_name):
        """컨테이너 내 PyTorch 설치 확인"""
        try:
            result = subprocess.run(
                ["docker", "exec", container_name, "python", "-c", 
                 "import torch; print(f'PyTorch 버전: {torch.__version__}')"],
                capture_output=True, text=True, check=True
            )
            print(f"{Colors.GREEN}✅ PyTorch 설치 확인됨{Colors.NC}")
            print(f"{Colors.CYAN}   {result.stdout.strip()}{Colors.NC}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.RED}❌ PyTorch 미설치{Colors.NC}")
            return False
            
    def find_container(self):
        """적절한 컨테이너 자동 감지"""
        containers_to_check = [
            "movie-mlops-pytorch", 
            "movie-mlops-api", 
            "movie-mlops-jupyter", 
            "movie-mlops-mlflow"
        ]
        
        print(f"{Colors.YELLOW}🤖 자동으로 적절한 컨테이너 감지 중...{Colors.NC}")
        
        for container in containers_to_check:
            if self.check_container_status(container):
                if self.check_pytorch_installation(container):
                    self.target_container = container
                    print(f"{Colors.GREEN}✅ 사용할 컨테이너: {container}{Colors.NC}")
                    return True
                    
        print(f"{Colors.RED}❌ PyTorch가 설치된 실행 중인 컨테이너를 찾을 수 없습니다.{Colors.NC}")
        print(f"{Colors.YELLOW}💡 다음 중 하나를 실행해보세요:{Colors.NC}")
        print("   ./run_movie_mlops.sh (메뉴에서 2번 또는 7번 선택)")
        print("   docker-compose -f docker/docker-compose.ml.yml up -d")
        return False
        
    def run_ml_pipeline(self, epochs=3):
        """ML 파이프라인 실행"""
        print(f"{Colors.CYAN}🚀 {self.target_container}에서 ML 파이프라인 실행 시작...{Colors.NC}")
        print(f"{Colors.YELLOW}📊 훈련 에포크: {epochs}{Colors.NC}")
        
        # ML 파이프라인 Python 코드
        ml_code = f'''
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from src.dataset.watch_log import get_datasets
from src.model.movie_predictor import MoviePredictor
from src.train.train import train
from src.evaluate.evaluate import evaluate
import time

print("=" * 60)
print("🎬 ML 파이프라인 시작")
print("=" * 60)
print(f"🔥 PyTorch 버전: {{torch.__version__}}")
print(f"💻 디바이스: {{'CUDA' if torch.cuda.is_available() else 'CPU'}}")

try:
    # 1. 데이터셋 로드
    print("\\n📊 1단계: 데이터셋 로드 중...")
    start_time = time.time()
    train_dataset, val_dataset, test_dataset = get_datasets()
    load_time = time.time() - start_time
    print(f"✅ 데이터셋 로드 완료 ({{load_time:.2f}}초)")
    print(f"   📈 훈련 데이터: {{len(train_dataset):,}}개")
    print(f"   📊 검증 데이터: {{len(val_dataset):,}}개")
    print(f"   🧪 테스트 데이터: {{len(test_dataset):,}}개")
    print(f"   🔢 특성 차원: {{train_dataset.features_dim}}")
    print(f"   🎯 클래스 수: {{train_dataset.num_classes}}")

    # 2. 데이터 로더 생성
    print("\\n🔄 2단계: 데이터 로더 생성 중...")
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    print("✅ 데이터 로더 생성 완료")

    # 3. 모델 생성
    print("\\n🧠 3단계: 모델 생성 중...")
    model = MoviePredictor(
        input_dim=train_dataset.features_dim,
        num_classes=train_dataset.num_classes
    )
    total_params = sum(p.numel() for p in model.parameters())
    print(f"✅ 모델 생성 완료")
    print(f"   📊 총 파라미터: {{total_params:,}}개")

    # 4. 모델 훈련
    print(f"\\n🎯 4단계: 모델 훈련 시작 (에포크: {epochs})...")
    train_start_time = time.time()
    trained_model = train(model, train_loader, val_loader, epochs={epochs})
    train_time = time.time() - train_start_time
    print(f"✅ 모델 훈련 완료 ({{train_time:.2f}}초)")

    # 5. 모델 평가
    print("\\n📊 5단계: 모델 평가 시작...")
    eval_start_time = time.time()
    test_accuracy = evaluate(trained_model, test_loader)
    eval_time = time.time() - eval_start_time
    
    total_time = time.time() - start_time
    
    print("\\n" + "=" * 60)
    print("📈 ML 파이프라인 완료 - 결과 요약")
    print("=" * 60)
    print(f"⏱️  총 실행 시간: {{total_time:.2f}}초")
    print(f"🎯 최종 정확도: {{test_accuracy:.4f}} ({{test_accuracy*100:.2f}}%)")
    print(f"📦 모델 크기: {{total_params:,}} 파라미터")
    print("=" * 60)
    print("🎬 ML 파이프라인 성공적으로 완료!")
    print("=" * 60)
    
except Exception as e:
    print(f"\\n❌ 오류 발생: {{str(e)}}")
    import traceback
    traceback.print_exc()
    exit(1)
'''
        
        try:
            # Docker 명령 실행
            result = subprocess.run(
                ["docker", "exec", "-it", self.target_container, "python", "-c", ml_code],
                cwd=self.project_root,
                check=True
            )
            
            print(f"{Colors.GREEN}🎉 ML 파이프라인 실행 완료!{Colors.NC}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}💥 ML 파이프라인 실행 실패!{Colors.NC}")
            print(f"{Colors.RED}오류: {e}{Colors.NC}")
            return False
            
    def main(self):
        """메인 실행 함수"""
        parser = argparse.ArgumentParser(description="Movie-MLOps ML 파이프라인 실행기")
        parser.add_argument("-c", "--container", help="대상 컨테이너 이름")
        parser.add_argument("-e", "--epochs", type=int, default=3, help="훈련 에포크 수 (기본값: 3)")
        
        args = parser.parse_args()
        
        self.print_banner()
        
        # 컨테이너 설정
        if args.container:
            self.target_container = args.container
            if not self.check_container_status(self.target_container):
                sys.exit(1)
            if not self.check_pytorch_installation(self.target_container):
                sys.exit(1)
        else:
            if not self.find_container():
                sys.exit(1)
                
        # 에포크 검증
        if args.epochs < 1:
            print(f"{Colors.RED}❌ 에포크 수는 1 이상이어야 합니다.{Colors.NC}")
            sys.exit(1)
            
        print(f"{Colors.GREEN}🎯 설정 확인:{Colors.NC}")
        print(f"   📦 컨테이너: {self.target_container}")
        print(f"   🔄 에포크: {args.epochs}")
        print()
        
        # 사용자 확인
        try:
            response = input(f"{Colors.YELLOW}계속 진행하시겠습니까? [Y/n]: {Colors.NC}")
            if response.lower() in ['n', 'no']:
                print(f"{Colors.YELLOW}⏹️  사용자에 의해 취소되었습니다.{Colors.NC}")
                sys.exit(0)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⏹️  사용자에 의해 취소되었습니다.{Colors.NC}")
            sys.exit(0)
            
        # ML 파이프라인 실행
        if self.run_ml_pipeline(args.epochs):
            print(f"{Colors.GREEN}🎉 모든 작업이 성공적으로 완료되었습니다!{Colors.NC}")
            print(f"{Colors.CYAN}📊 결과를 확인하려면 다음 URL을 방문하세요:{Colors.NC}")
            print("   MLflow: http://localhost:5000")
            print("   API 테스트: http://localhost:8000/docs")
        else:
            print(f"{Colors.RED}💥 ML 파이프라인 실행에 실패했습니다.{Colors.NC}")
            sys.exit(1)

if __name__ == "__main__":
    runner = MLPipelineRunner()
    runner.main()
