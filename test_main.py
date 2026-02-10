#!/usr/bin/env python
"""main.py를 테스트하기 위한 스크립트"""
import sys
import signal

print("="*60)
print("Testing main.py execution...")
print("="*60)

# 10초 후 강제 종료
def timeout_handler(signum, frame):
    print("\n" + "="*60)
    print("TIMEOUT: 10초 경과, 프로그램을 중단합니다")
    print("="*60)
    sys.exit(0)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)

try:
    import main
    print("\nCalling main.main()...")
    main.main()
except KeyboardInterrupt:
    print("\n\nKeyboardInterrupt caught")
except SystemExit:
    print("\n\nSystemExit caught")
except Exception as e:
    print(f"\n\nException caught: {e}")
    import traceback
    traceback.print_exc()
