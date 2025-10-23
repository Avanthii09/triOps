#!/usr/bin/env python3
"""
Generate gRPC Python files from proto definitions
"""

import subprocess
import sys
import os

def generate_grpc_files():
    """Generate Python gRPC files from proto definitions."""
    proto_dir = "proto"
    proto_file = "chatbot.proto"
    
    if not os.path.exists(os.path.join(proto_dir, proto_file)):
        print(f"Error: {proto_file} not found in {proto_dir}/")
        return False
    
    try:
        # Generate Python files from proto
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out=.",
            f"--grpc_python_out=.",
            f"{proto_dir}/{proto_file}"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ gRPC Python files generated successfully!")
            print("Generated files:")
            print("  - chatbot_pb2.py")
            print("  - chatbot_pb2_grpc.py")
            return True
        else:
            print(f"❌ Error generating gRPC files:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"❌ Exception during gRPC generation: {e}")
        return False

if __name__ == "__main__":
    success = generate_grpc_files()
    if success:
        print("\n🎉 gRPC files ready! You can now run the gRPC server.")
    else:
        print("\n💥 Failed to generate gRPC files. Please check the error messages above.")
        sys.exit(1)

