{{- define "cray-ipxe.deployment" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "cray-service.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ include "cray-service.name" . }}
    {{- include "cray-service.common-labels" . | nindent 4 }}
  annotations:
    {{- include "cray-service.common-annotations" . | nindent 4 }}
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "cray-service.name" . }}
      app.kubernetes.io/instance: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "cray-service.name" . }}
        app.kubernetes.io/instance: {{ .Release.Name }}
        app.kubernetes.io/version: {{ .Chart.AppVersion }}
      annotations:
        {{- include "cray-service.pod-annotations" . | nindent 8 }}
    spec:
      {{- include "cray-service.common-spec" . | nindent 6 }}
{{- end -}}