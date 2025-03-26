from passlib.context import CryptContext
import sys

# 创建一个与主应用相同的CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

if __name__ == "__main__":
    # 如果命令行提供了密码，则使用它，否则使用默认密码
    password = sys.argv[1] if len(sys.argv) > 1 else "admin123"
    hashed = get_password_hash(password)
    print(f"原始密码: {password}")
    print(f"哈希密码: {hashed}")
    
    # 验证哈希
    is_valid = pwd_context.verify(password, hashed)
    print(f"验证结果: {is_valid}") 