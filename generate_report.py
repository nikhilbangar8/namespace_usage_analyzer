import json
import os
from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import sys
import subprocess
from collections import defaultdict

def get_pod_usage_kubectl(namespace):
    try:
        cmd = ["kubectl", "top", "pods", "-n", namespace, "--containers", "--no-headers"]
        output = subprocess.check_output(cmd, text=True)
        usage_data = defaultdict(lambda: {})
        
        for line in output.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 4:
                pod_name = parts[0]
                container_name = parts[1]
                cpu = parts[2]
                memory = parts[3]
                
                usage_data[pod_name][container_name]= {
                    "cpu_usage": cpu,
                    "memory_usage": memory
                }
        return dict(usage_data)
    except subprocess.CalledProcessError as e:
        print(f"Error running kubectl top: {e}")
        return {}

def load_k8s_config():
    config.load_kube_config()

def get_pod_data(namespace):
    v1 = client.CoreV1Api()
    pod_data = []

    try:
        pods = v1.list_namespaced_pod(namespace)
        for pod in pods.items:
            pod_info = {
                'pod_name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'containers': []
            }
            for container in pod.spec.containers:
                container_info = {
                    'container_name': container.name,
                    'requests': {
                        'cpu': container.resources.requests.get('cpu', 'N/A') if container.resources.requests else 'N/A',
                        'memory': container.resources.requests.get('memory', 'N/A') if container.resources.requests else 'N/A'
                    },
                    'limits': {
                        'cpu': container.resources.limits.get('cpu', 'N/A') if container.resources.limits else 'N/A',
                        'memory': container.resources.limits.get('memory', 'N/A') if container.resources.limits else 'N/A'
                    }
                }
                pod_info['containers'].append(container_info)
            pod_data.append(pod_info)
    except ApiException as e:
        print(f"Error fetching pod data: {e}")
    return pod_data

def get_pod_usage(namespace):
    metrics = client.MetricsV1beta1Api()
    usage_data = {}
    try:
        pod_metrics = metrics.list_namespaced_pod_metrics(namespace)
        for pod in pod_metrics.items:
            usage = {}
            for container in pod.containers:
                usage[container.name] = {
                    'cpu_usage': container.usage.get('cpu', 'N/A'),
                    'memory_usage': container.usage.get('memory', 'N/A')
                }
            usage_data[pod.metadata.name] = usage
    except ApiException as e:
        print(f"Error fetching metrics: {e}")
    return usage_data


def combine_pod_data_and_usage(pod_data, usage_data):
    for pod in pod_data:
        for container in pod['containers']:
            usage = usage_data.get(pod['pod_name'], {}).get(container['container_name'], {})
            # print(usage,pod['pod_name'])
            container['cpu_usage'] = usage.get('cpu_usage', 'N/A')
            container['memory_usage'] = usage.get('memory_usage', 'N/A')
    return pod_data

def save_report(data,context, namespace):
    timestamp = datetime.now().strftime('%Y%m%d-%H%M')
    filename = f"report-{context}-{namespace}-{timestamp}.json"
    os.makedirs('output', exist_ok=True)
    filepath = os.path.join('output', filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Report saved to {filepath}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_report.py <context> <namespace>")
        sys.exit(1)

    context = sys.argv[1]
    namespace = sys.argv[2]

    try:
        config.load_kube_config(context=context)
        print(f"Loaded Kubernetes config with context: {context}")
    except Exception as e:
        print(f"Error loading kubeconfig with context '{context}': {e}")
        sys.exit(1)
    
    pod_data = get_pod_data(namespace)
    
    with open("output/pod_data.json", 'w') as f:
        json.dump(pod_data, f, indent=2)

    if not pod_data:
        print(f"No pods found in namespace '{namespace}'.")
        return

    usage_data = get_pod_usage_kubectl(namespace)

    with open("output/usage_data.json", 'w') as f:
        json.dump(usage_data, f, indent=2)

    combined = combine_pod_data_and_usage(pod_data, usage_data)
    save_report(combined, context, namespace)

if __name__ == "__main__":
    main()
