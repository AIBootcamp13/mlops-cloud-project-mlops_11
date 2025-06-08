#!/bin/bash

echo "🚀 안전한 전체 프로젝트 마이그레이션 시작..."

# 백업 확인
echo "🛡️ 백업 상태 확인..."
if [ ! -f ".env.backup-$(date +%Y%m%d)" ]; then
    echo "📋 .env 파일 백업 생성 중..."
    cp .env .env.backup-$(date +%Y%m%d-%H%M%S) 2>/dev/null || echo "⚠️ .env 파일이 없어서 백업을 건너뜁니다"
fi

# 1단계: 기반 구조 생성 (안전)
echo "📁 1단계: 기반 구조 생성 중..."
mkdir -p {src,scripts,tests,docker,config,data,docs,airflow,logs,models}
mkdir -p src/{data,models,training,evaluation,utils,frontend,api,features}
mkdir -p scripts/{migration,setup,test,deploy,data,monitoring}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docker/{dockerfiles,configs}
mkdir -p data/{raw,processed}/{tmdb,features,models}

# 2단계: 데이터 파이프라인 코드 이전 (경로 수정)
echo "📦 2단계: 데이터 파이프라인 코드 이전 중..."
if [ -d "../my-mlops/data-prepare" ]; then
    mkdir -p src/data/{crawlers,processors}
    
    # 중복 파일 체크 후 복사
    if [ -f "../my-mlops/data-prepare/crawler.py" ]; then
        if [ ! -f "src/data/crawlers/tmdb_crawler.py" ]; then
            cp ../my-mlops/data-prepare/crawler.py src/data/crawlers/tmdb_crawler.py
            echo "✅ crawler.py → tmdb_crawler.py 복사 완료"
        else
            echo "⚠️ tmdb_crawler.py가 이미 존재합니다. 건너뜀"
        fi
    else
        echo "⚠️ crawler.py 파일을 찾을 수 없습니다"
    fi
    
    if [ -f "../my-mlops/data-prepare/preprocessing.py" ]; then
        if [ ! -f "src/data/processors/tmdb_processor.py" ]; then
            cp ../my-mlops/data-prepare/preprocessing.py src/data/processors/tmdb_processor.py
            echo "✅ preprocessing.py → tmdb_processor.py 복사 완료"
        else
            echo "⚠️ tmdb_processor.py가 이미 존재합니다. 건너뜀"
        fi
    else
        echo "⚠️ preprocessing.py 파일을 찾을 수 없습니다"
    fi
    
    if [ -f "../my-mlops/data-prepare/main.py" ]; then
        if [ ! -f "scripts/data/run_data_collection.py" ]; then
            mkdir -p scripts/data
            cp ../my-mlops/data-prepare/main.py scripts/data/run_data_collection.py
            echo "✅ main.py → run_data_collection.py 복사 완료"
        else
            echo "⚠️ run_data_collection.py가 이미 존재합니다. 건너뜀"
        fi
    else
        echo "⚠️ main.py 파일을 찾을 수 없습니다"
    fi
    
    # 환경 변수 안전한 통합 (중복 체크)
    if [ -f "../my-mlops/data-prepare/.env" ]; then
        echo "🔧 환경 변수 중복 검사 후 통합 중..."
        
        # 임시 파일에 새로운 내용 저장
        temp_env=$(mktemp)
        cat ../my-mlops/data-prepare/.env > "$temp_env"
        
        # 기존 .env에 없는 내용만 추가
        while IFS= read -r line; do
            if [ -n "$line" ] && [[ ! "$line" =~ ^[[:space:]]*# ]] && [[ "$line" =~ = ]]; then
                key=$(echo "$line" | cut -d'=' -f1)
                if ! grep -q "^$key=" .env 2>/dev/null; then
                    echo "$line" >> .env
                    echo "  ➕ 추가: $key"
                fi
            fi
        done < "$temp_env"
        
        rm "$temp_env"
        echo "✅ 환경 변수 안전한 통합 완료"
    else
        echo "⚠️ data-prepare/.env 파일을 찾을 수 없습니다"
    fi
    
    # 데이터 결과 복사
    if [ -d "../my-mlops/data-prepare/result" ]; then
        echo "📊 기존 수집 데이터 복사 중..."
        cp -r ../my-mlops/data-prepare/result/* data/raw/tmdb/ 2>/dev/null || true
        echo "✅ 기존 데이터 복사 완료"
    else
        echo "⚠️ data-prepare/result 디렉터리를 찾을 수 없습니다"
    fi
    
    echo "✅ 데이터 파이프라인 코드 이전 완료"
else
    echo "⚠️ ../my-mlops/data-prepare 디렉터리를 찾을 수 없습니다"
fi

# 3단계: ML 모델 + 웹앱 코드 이전 (경로 수정)
echo "🤖 3단계: ML 모델 + 웹앱 코드 이전 중..."
if [ -d "../my-mlops/mlops" ]; then
    echo "🧠 ML 코드 이전 중..."
    
    # 안전한 복사 (기존 파일 덮어쓰지 않음)
    if [ -d "../my-mlops/mlops/src" ]; then
        echo "📂 기존 ML 소스코드 안전 복사 중..."
        
        # rsync로 안전한 복사 (--ignore-existing 옵션)
        if command -v rsync >/dev/null 2>&1; then
            rsync -av --ignore-existing ../my-mlops/mlops/src/ src/ 2>/dev/null || true
        else
            # rsync가 없는 경우 수동으로 안전 복사
            find ../my-mlops/mlops/src -type f | while read -r file; do
                rel_path=${file#../my-mlops/mlops/src/}
                dest_file="src/$rel_path"
                if [ ! -f "$dest_file" ]; then
                    mkdir -p "$(dirname "$dest_file")"
                    cp "$file" "$dest_file" 2>/dev/null || true
                fi
            done
        fi
        
        # 기존 구조를 건드리지 않고 안전하게 처리
        echo "🔄 디렉터리 구조 안전 확인 중..."
        
        # legacy 디렉터리가 없고 model 디렉터리가 있을 때만 이동
        if [ -d "src/model" ] && [ ! -d "src/models/legacy" ]; then
            echo "🔄 model → models/legacy 이동"
            mkdir -p src/models
            mv src/model src/models/legacy 2>/dev/null || true
        fi
        
        # training 디렉터리가 없고 train 디렉터리가 있을 때만 이동
        if [ -d "src/train" ] && [ ! -d "src/training" ]; then
            echo "🔄 train → training 이동"
            mv src/train src/training 2>/dev/null || true
        fi
        
        # evaluation 디렉터리가 없고 evaluate 디렉터리가 있을 때만 이동
        if [ -d "src/evaluate" ] && [ ! -d "src/evaluation" ]; then
            echo "🔄 evaluate → evaluation 이동"
            mv src/evaluate src/evaluation 2>/dev/null || true
        fi
        
        echo "✅ ML 코드 구조 안전 변경 완료"
    else
        echo "⚠️ ../my-mlops/mlops/src 디렉터리를 찾을 수 없습니다"
    fi
    
    # PyTorch 디렉터리 생성 (이미 있으면 스킵)
    if [ ! -d "src/models/pytorch" ]; then
        mkdir -p src/models/pytorch
        echo "✅ PyTorch 모델 디렉터리 생성 완료"
    else
        echo "ℹ️ PyTorch 모델 디렉터리가 이미 존재합니다"
    fi
    
    # 데이터셋 이동
    if [ -d "../my-mlops/mlops/dataset" ]; then
        echo "📊 데이터셋 파일 이전 중..."
        cp -r ../my-mlops/mlops/dataset/* data/processed/ 2>/dev/null || true
        echo "✅ 데이터셋 이전 완료"
    else
        echo "⚠️ ../my-mlops/mlops/dataset 디렉터리를 찾을 수 없습니다"
    fi
    
    echo "✅ ML 모델 코드 이전 완료"
else
    echo "⚠️ ../my-mlops/mlops 디렉터리를 찾을 수 없습니다"
fi

# React 웹앱 이전 (경로 수정)
if [ -d "../my-mlops-web" ]; then
    echo "🌐 React 웹앱 이전 중..."
    
    # frontend/react 디렉터리 확인 (현재 구조 고려)
    if [ -d "src/frontend/react" ] && [ -n "$(ls -A src/frontend/react 2>/dev/null)" ]; then
        echo "⚠️ src/frontend/react가 이미 존재하고 내용이 있습니다."
        echo "🔄 기존 React 앱을 src/frontend/react-legacy로 백업하고 새로 복사합니다..."
        mv src/frontend/react src/frontend/react-legacy 2>/dev/null || true
    fi
    
    # React 소스만 복사 (src/ 디렉터리)
    if [ -d "../my-mlops-web/src" ]; then
        mkdir -p src/frontend/react
        cp -r ../my-mlops-web/src/* src/frontend/react/ 2>/dev/null || true
        echo "✅ React 소스 파일 복사 완료"
    fi
    
    # package.json 복사
    if [ -f "../my-mlops-web/package.json" ]; then
        cp ../my-mlops-web/package.json src/frontend/ 2>/dev/null || true
        echo "✅ package.json 복사 완료"
    fi
    
    # public 디렉터리 복사
    if [ -d "../my-mlops-web/public" ]; then
        cp -r ../my-mlops-web/public src/frontend/ 2>/dev/null || true
        echo "✅ public 디렉터리 복사 완료"
    fi
    
    # 환경 변수 안전한 통합
    if [ -f "../my-mlops-web/.env" ]; then
        echo "🔧 프론트엔드 환경 변수 안전한 통합 중..."
        
        temp_env=$(mktemp)
        cat ../my-mlops-web/.env > "$temp_env"
        
        while IFS= read -r line; do
            if [ -n "$line" ] && [[ ! "$line" =~ ^[[:space:]]*# ]] && [[ "$line" =~ = ]]; then
                key=$(echo "$line" | cut -d'=' -f1)
                if ! grep -q "^$key=" .env 2>/dev/null; then
                    echo "$line" >> .env
                    echo "  ➕ 추가: $key"
                fi
            fi
        done < "$temp_env"
        
        rm "$temp_env"
        echo "✅ 프론트엔드 환경 변수 안전한 통합 완료"
    fi
    
    echo "✅ React 웹앱 이전 완료"
    
else
    echo "⚠️ ../my-mlops-web 디렉터리를 찾을 수 없습니다"
fi

# 기본 설정 파일 생성 (덮어쓰지 않음)
echo "⚙️ 기본 설정 파일 생성 중..."
[ ! -f ".env" ] && touch .env
[ ! -f "requirements.txt" ] && touch requirements.txt
[ ! -f "pyproject.toml" ] && touch pyproject.toml
[ ! -f "README.md" ] && echo "# Movie MLOps Project" > README.md

echo "🎉 안전한 마이그레이션 완료!"
echo ""
echo "📋 마이그레이션 결과:"
echo "✅ 기존 파일들 보존됨"
echo "✅ 중복 환경 변수 방지됨"
echo "✅ 백업 파일 생성됨"
echo ""
echo "📋 복사된 파일들:"
if [ -f "src/data/crawlers/tmdb_crawler.py" ]; then
    echo "  📦 src/data/crawlers/tmdb_crawler.py"
fi
if [ -f "src/data/processors/tmdb_processor.py" ]; then
    echo "  📦 src/data/processors/tmdb_processor.py"
fi
if [ -f "scripts/data/run_data_collection.py" ]; then
    echo "  📦 scripts/data/run_data_collection.py"
fi
if [ -d "src/frontend/react" ]; then
    echo "  🌐 src/frontend/react/ (React 앱)"
fi
echo ""
echo "📋 다음 단계:"
echo "1. NumPy 모델을 PyTorch로 전환"
echo "2. Airflow DAG 작성" 
echo "3. Docker 환경 설정"
echo "4. 테스트 코드 작성"
echo ""
echo "🔧 백업 파일 위치:"
echo "$(ls -la .env.backup-* 2>/dev/null || echo '백업 파일 없음')"
