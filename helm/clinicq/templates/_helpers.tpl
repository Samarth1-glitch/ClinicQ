{{- define "clinicq.name" -}}
{{- .Release.Name | trunc 40 | trimSuffix "-" -}}
{{- end -}}

{{- define "clinicq.labels" -}}
app.kubernetes.io/part-of: clinicq
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "clinicq.backendSelector" -}}
app.kubernetes.io/name: clinicq-backend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "clinicq.frontendSelector" -}}
app.kubernetes.io/name: clinicq-frontend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "clinicq.postgresSelector" -}}
app.kubernetes.io/name: clinicq-postgres
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
