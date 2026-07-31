{{- /* The whole archive as one markdown file, newest first. */ -}}
# {{ site.Title }}
{{ with site.Params.description }}{{ . }}{{ end }}
Exported {{ now.Format "2 January 2006" }} from {{ site.BaseURL }}

{{ $posts := (where site.RegularPages "Type" "post").ByDate.Reverse }}
{{ len $posts }} posts.

{{ range $posts }}
---

## {{ with .Title }}{{ . }}{{ else }}{{ .Date.Format "2 January 2006" }}{{ end }}

*{{ .Date.Format "2 January 2006" }}*{{ with .Params.categories }} · {{ delimit . ", " }}{{ end }}
{{ .Permalink }}

{{ .RawContent }}
{{ end }}
