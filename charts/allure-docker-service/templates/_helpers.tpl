{{/*
Expand the name of the chart.
*/}}
{{- define "allure-docker-service.name" -}}
{{- default .Chart.Name .Values.global.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
Truncated at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "allure-docker-service.fullname" -}}
{{- if .Values.global.fullnameOverride }}
{{- .Values.global.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.global.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart label.
*/}}
{{- define "allure-docker-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels (chart-wide, used for resources that span components such as ServiceAccount).
*/}}
{{- define "allure-docker-service.commonLabels" -}}
helm.sh/chart: {{ include "allure-docker-service.chart" . }}
app.kubernetes.io/name: {{ include "allure-docker-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
ServiceAccount name.
*/}}
{{- define "allure-docker-service.serviceAccountName" -}}
{{- if .Values.global.serviceAccount.create }}
{{- default (include "allure-docker-service.fullname" .) .Values.global.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.global.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* ------------------------------------------------------------------ */}}
{{/*  API component                                                       */}}
{{/* ------------------------------------------------------------------ */}}

{{/*
API fully-qualified name.
*/}}
{{- define "allure-docker-service.api.fullname" -}}
{{- printf "%s-api" (include "allure-docker-service.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
API selector labels.
*/}}
{{- define "allure-docker-service.api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "allure-docker-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: api
{{- end }}

{{/*
API labels (selector labels + chart metadata).
*/}}
{{- define "allure-docker-service.api.labels" -}}
helm.sh/chart: {{ include "allure-docker-service.chart" . }}
{{ include "allure-docker-service.api.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
API image reference — prepends the global registry when set.
Falls back to Chart.AppVersion when image.tag is not specified.
*/}}
{{- define "allure-docker-service.api.image" -}}
{{- $registry := .Values.global.image.registry -}}
{{- $repo     := .Values.api.image.repository -}}
{{- $tag      := .Values.api.image.tag | default .Chart.AppVersion -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repo $tag -}}
{{- else -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}
{{- end }}

{{/* ------------------------------------------------------------------ */}}
{{/*  UI component                                                        */}}
{{/* ------------------------------------------------------------------ */}}

{{/*
UI fully-qualified name.
*/}}
{{- define "allure-docker-service.ui.fullname" -}}
{{- printf "%s-ui" (include "allure-docker-service.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
UI selector labels.
*/}}
{{- define "allure-docker-service.ui.selectorLabels" -}}
app.kubernetes.io/name: {{ include "allure-docker-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: ui
{{- end }}

{{/*
UI labels (selector labels + chart metadata).
*/}}
{{- define "allure-docker-service.ui.labels" -}}
helm.sh/chart: {{ include "allure-docker-service.chart" . }}
{{ include "allure-docker-service.ui.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
UI image reference — prepends the global registry when set.
Falls back to Chart.AppVersion when image.tag is not specified.
*/}}
{{- define "allure-docker-service.ui.image" -}}
{{- $registry := .Values.global.image.registry -}}
{{- $repo     := .Values.ui.image.repository -}}
{{- $tag      := .Values.ui.image.tag | default .Chart.AppVersion -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repo $tag -}}
{{- else -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}
{{- end }}
