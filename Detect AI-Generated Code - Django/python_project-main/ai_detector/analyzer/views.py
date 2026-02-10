from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .utils import clone_repo, scan_ai_plag, cleanup_repo
import os


@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeView(View):
    def post(self, request):
        repo_url = request.POST.get('repo_url')  #save url
        if not repo_url:    # url nahi takli
            return JsonResponse({'error': 'No repo URL provided'})
   # takli
        local_path = None
        try:
            print(f"Cloning {repo_url}...")
            local_path = clone_repo(repo_url)  # function call and local path save return value of this function

            print("Scanning...")
            results = scan_ai_plag(local_path)

            ai_score = results['overall_ai_score']
            plag_score = results['overall_plag_score']
            verdict = '🚨 AI/Copied' if ai_score > 0.6 or plag_score > 0.3 else '✅ Likely Human'
            results['verdict'] = verdict
            return JsonResponse(results)

        except Exception as e:
            return JsonResponse({'error': f'Scan failed: {str(e)}'})
        finally:
            if local_path and os.path.exists(local_path):
                cleanup_repo(local_path)


class IndexView(View):
    def get(self, request):
        return render(request, 'analyzer/index.html')
