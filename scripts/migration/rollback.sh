#!/bin/bash
echo "🔄 마이그레이션 롤백 시작..."

BACKUP_DATE=${1:-$(date +%Y%m%d)}
BACKUP_DIR="backups"

echo "📅 롤백 대상 날짜: $BACKUP_DATE"
echo "📂 백업 디렉터리: $BACKUP_DIR"

# 백업 디렉터리 확인
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 백업 디렉터리가 존재하지 않습니다: $BACKUP_DIR"
    echo "💡 마이그레이션 전에 백업을 생성했는지 확인하세요."
    exit 1
fi

# my-mlops 롤백
if [ -d "$BACKUP_DIR/my-mlops-$BACKUP_DATE" ]; then
    echo "📦 백업에서 my-mlops 복원 중..."
    
    # 기존 디렉터리 백업 (롤백 전 상태 보존)
    if [ -d "my-mlops" ]; then
        echo "🗂️ 현재 my-mlops를 my-mlops-rollback-$(date +%H%M%S)로 백업"
        mv my-mlops "my-mlops-rollback-$(date +%H%M%S)"
    fi
    
    # 백업에서 복원
    cp -r "$BACKUP_DIR/my-mlops-$BACKUP_DATE" my-mlops
    echo "✅ my-mlops 복원 완료"
else
    echo "⚠️ my-mlops-$BACKUP_DATE 백업을 찾을 수 없습니다"
fi

# my-mlops-web 롤백
if [ -d "$BACKUP_DIR/my-mlops-web-$BACKUP_DATE" ]; then
    echo "🌐 백업에서 my-mlops-web 복원 중..."
    
    # 기존 디렉터리 백업 (롤백 전 상태 보존)
    if [ -d "my-mlops-web" ]; then
        echo "🗂️ 현재 my-mlops-web을 my-mlops-web-rollback-$(date +%H%M%S)로 백업"
        mv my-mlops-web "my-mlops-web-rollback-$(date +%H%M%S)"
    fi
    
    # 백업에서 복원
    cp -r "$BACKUP_DIR/my-mlops-web-$BACKUP_DATE" my-mlops-web
    echo "✅ my-mlops-web 복원 완료"
else
    echo "⚠️ my-mlops-web-$BACKUP_DATE 백업을 찾을 수 없습니다"
fi

# 마이그레이션된 파일들 정리 (선택사항)
read -p "🗑️ 마이그레이션으로 생성된 파일들을 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 마이그레이션 파일 정리 중..."
    
    # 마이그레이션으로 생성된 디렉터리들 삭제
    rm -rf src/data/crawlers 2>/dev/null || true
    rm -rf src/data/processors 2>/dev/null || true
    rm -rf src/models/legacy 2>/dev/null || true
    rm -rf src/models/pytorch 2>/dev/null || true
    rm -rf src/frontend 2>/dev/null || true
    rm -rf scripts/data/run_data_collection.py 2>/dev/null || true
    
    echo "✅ 마이그레이션 파일 정리 완료"
else
    echo "📝 마이그레이션 파일들이 보존되었습니다"
fi

# 환경 변수 롤백 (선택사항)
if [ -f ".env.backup-$BACKUP_DATE" ]; then
    read -p "🔧 환경 변수 파일을 롤백하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp ".env.backup-$BACKUP_DATE" .env
        echo "✅ 환경 변수 롤백 완료"
    fi
fi

echo ""
echo "🔄 롤백 작업 완료!"
echo ""
echo "📋 롤백 후 확인사항:"
echo "1. my-mlops/ 디렉터리 구조 확인"
echo "2. my-mlops-web/ 디렉터리 구조 확인"  
echo "3. 기존 작업 환경이 정상인지 테스트"
echo "4. 필요시 백업 디렉터리에서 추가 파일 복원"
echo ""
echo "💡 사용 가능한 백업 목록:"
ls -la "$BACKUP_DIR" 2>/dev/null || echo "백업이 없습니다"
