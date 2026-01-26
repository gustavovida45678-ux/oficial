#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Trading Chart Analysis System
Tests CALL/PUT image annotation functionality
"""
import requests
import sys
import json
import os
from datetime import datetime
from pathlib import Path

class TradingAPITester:
    def __init__(self, base_url="https://192f7439-67c1-4c06-8cd5-b18ce54dd85a.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test image path
        self.test_image_path = "/app/backend/test_chart.png"
        if not os.path.exists(self.test_image_path):
            # Create a simple test image if it doesn't exist
            self._create_test_image()

    def _create_test_image(self):
        """Create a simple test image for testing"""
        from PIL import Image, ImageDraw
        import io
        
        # Create a simple chart-like image
        img = Image.new('RGB', (800, 600), color='black')
        draw = ImageDraw.Draw(img)
        
        # Draw some chart-like elements
        draw.rectangle([100, 100, 700, 500], outline='white', width=2)
        draw.line([150, 450, 250, 350, 350, 400, 450, 300, 550, 350, 650, 250], fill='green', width=3)
        
        # Save the test image
        img.save(self.test_image_path, 'PNG')
        print(f"✅ Created test image: {self.test_image_path}")

    def run_test(self, name, test_func):
        """Run a single test and record results"""
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            success, details = test_func()
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - {name}")
                status = "PASSED"
            else:
                print(f"❌ FAILED - {name}")
                print(f"   Details: {details}")
                status = "FAILED"
            
            self.test_results.append({
                "test_name": name,
                "status": status,
                "details": details,
                "timestamp": datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            print(f"❌ ERROR - {name}: {str(e)}")
            self.test_results.append({
                "test_name": name,
                "status": "ERROR",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False

    def test_api_health(self):
        """Test if API is running"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            if response.status_code == 200:
                return True, "API is running"
            else:
                return False, f"API returned status {response.status_code}"
        except Exception as e:
            return False, f"API connection failed: {str(e)}"

    def test_chat_endpoint(self):
        """Test basic chat endpoint"""
        try:
            payload = {"message": "Hello, test message"}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(f"{self.api_url}/chat", json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'user_message' in data and 'assistant_message' in data:
                    return True, "Chat endpoint working correctly"
                else:
                    return False, "Response missing required fields"
            else:
                return False, f"Status code: {response.status_code}, Response: {response.text}"
                
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_single_image_analysis(self):
        """Test single image analysis with CALL/PUT generation"""
        try:
            if not os.path.exists(self.test_image_path):
                return False, f"Test image not found: {self.test_image_path}"
            
            # Prepare request with trading-specific question
            question = """Faça uma análise técnica COMPLETA deste gráfico.
            INCLUA OBRIGATORIAMENTE:
            1. Recomendação CLARA: COMPRA (CALL) ou VENDA (PUT)
            2. Níveis de entrada com valores numéricos
            3. Stop loss e take profit
            4. Percentual de confiança
            Forneça uma RECOMENDAÇÃO DEFINITIVA ao final."""
            
            files = {'file': ('test_chart.png', open(self.test_image_path, 'rb'), 'image/png')}
            data = {'question': question}
            
            response = requests.post(f"{self.api_url}/chat/image", files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check required fields
                required_fields = ['image_id', 'image_path', 'user_message', 'assistant_message']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    return False, f"Missing fields: {missing_fields}"
                
                # Check for CALL and PUT annotated paths
                has_call_paths = result.get('call_annotated_path') is not None
                has_put_paths = result.get('put_annotated_path') is not None
                
                details = {
                    "image_id": result.get('image_id'),
                    "has_call_annotated": has_call_paths,
                    "has_put_annotated": has_put_paths,
                    "call_path": result.get('call_annotated_path'),
                    "put_path": result.get('put_annotated_path'),
                    "analysis_length": len(result.get('assistant_message', {}).get('content', ''))
                }
                
                if has_call_paths and has_put_paths:
                    return True, f"Both CALL and PUT images generated successfully: {details}"
                else:
                    return False, f"Missing CALL or PUT images: {details}"
                    
            else:
                return False, f"Status code: {response.status_code}, Response: {response.text}"
                
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_multiple_images_analysis(self):
        """Test multiple images analysis with CALL/PUT generation"""
        try:
            if not os.path.exists(self.test_image_path):
                return False, f"Test image not found: {self.test_image_path}"
            
            question = "Analise estes gráficos e forneça recomendações CALL ou PUT para cada um."
            
            # Send the same image twice to test multiple image handling
            files = [
                ('files', ('test_chart1.png', open(self.test_image_path, 'rb'), 'image/png')),
                ('files', ('test_chart2.png', open(self.test_image_path, 'rb'), 'image/png'))
            ]
            data = {'question': question}
            
            response = requests.post(f"{self.api_url}/chat/images", files=files, data=data, timeout=90)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check required fields
                required_fields = ['image_ids', 'image_paths', 'user_message', 'assistant_message']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    return False, f"Missing fields: {missing_fields}"
                
                # Check for CALL and PUT annotated paths arrays
                call_paths = result.get('call_annotated_paths', [])
                put_paths = result.get('put_annotated_paths', [])
                
                details = {
                    "image_count": len(result.get('image_ids', [])),
                    "call_paths_count": len([p for p in call_paths if p]),
                    "put_paths_count": len([p for p in put_paths if p]),
                    "call_paths": call_paths,
                    "put_paths": put_paths
                }
                
                if len(call_paths) > 0 and len(put_paths) > 0:
                    return True, f"Multiple images with CALL/PUT generated: {details}"
                else:
                    return False, f"Missing CALL or PUT images for multiple images: {details}"
                    
            else:
                return False, f"Status code: {response.status_code}, Response: {response.text}"
                
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_image_files_exist(self):
        """Test if generated annotated images actually exist on disk"""
        try:
            # First generate some images
            if not os.path.exists(self.test_image_path):
                return False, "Test image not found"
            
            question = "Análise técnica com recomendação CALL ou PUT"
            files = {'file': ('test_chart.png', open(self.test_image_path, 'rb'), 'image/png')}
            data = {'question': question}
            
            response = requests.post(f"{self.api_url}/chat/image", files=files, data=data, timeout=60)
            
            if response.status_code != 200:
                return False, f"Failed to generate images: {response.status_code}"
            
            result = response.json()
            call_path = result.get('call_annotated_path')
            put_path = result.get('put_annotated_path')
            
            if not call_path or not put_path:
                return False, "No annotated paths returned"
            
            # Check if files exist on disk (remove leading slash for local path)
            call_file_path = f"/app/backend{call_path}"
            put_file_path = f"/app/backend{put_path}"
            
            call_exists = os.path.exists(call_file_path)
            put_exists = os.path.exists(put_file_path)
            
            details = {
                "call_path": call_path,
                "put_path": put_path,
                "call_file_exists": call_exists,
                "put_file_exists": put_exists,
                "call_file_path": call_file_path,
                "put_file_path": put_file_path
            }
            
            if call_exists and put_exists:
                return True, f"Both CALL and PUT image files exist: {details}"
            else:
                return False, f"Image files missing: {details}"
                
        except Exception as e:
            return False, f"File check failed: {str(e)}"

    def test_image_generation(self):
        """Test image generation endpoint"""
        try:
            payload = {
                "prompt": "A simple trading chart with candlesticks",
                "number_of_images": 1
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(f"{self.api_url}/generate-image", json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ['image_id', 'image_path', 'image_base64']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    return False, f"Missing fields: {missing_fields}"
                
                return True, "Image generation working correctly"
            else:
                return False, f"Status code: {response.status_code}, Response: {response.text}"
                
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_messages_endpoints(self):
        """Test messages GET and DELETE endpoints"""
        try:
            # Test GET messages
            response = requests.get(f"{self.api_url}/messages", timeout=10)
            if response.status_code != 200:
                return False, f"GET messages failed: {response.status_code}"
            
            messages = response.json()
            if not isinstance(messages, list):
                return False, "Messages should return a list"
            
            # Test DELETE messages (optional - only if we want to clear)
            # response = requests.delete(f"{self.api_url}/messages", timeout=10)
            # if response.status_code != 200:
            #     return False, f"DELETE messages failed: {response.status_code}"
            
            return True, f"Messages endpoints working, found {len(messages)} messages"
            
        except Exception as e:
            return False, f"Messages test failed: {str(e)}"

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Trading API Comprehensive Tests")
        print(f"🔗 Base URL: {self.base_url}")
        print(f"📊 Test Image: {self.test_image_path}")
        print("=" * 80)
        
        # Run all tests
        tests = [
            ("API Health Check", self.test_api_health),
            ("Chat Endpoint", self.test_chat_endpoint),
            ("Single Image Analysis (CALL/PUT)", self.test_single_image_analysis),
            ("Multiple Images Analysis (CALL/PUT)", self.test_multiple_images_analysis),
            ("Generated Image Files Exist", self.test_image_files_exist),
            ("Image Generation", self.test_image_generation),
            ("Messages Endpoints", self.test_messages_endpoints),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [r for r in self.test_results if r['status'] != 'PASSED']
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test_name']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = TradingAPITester()
    success = tester.run_all_tests()
    
    # Save test results
    results_file = f"/app/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "total_tests": tester.tests_run,
                "passed_tests": tester.tests_passed,
                "failed_tests": tester.tests_run - tester.tests_passed,
                "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": tester.test_results
        }, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())