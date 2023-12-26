package main

//go:generate go run directives_generate.go

import (
	"net/http"
	_ "ohmydns/core/plugin" // Plug in CoreDNS.
	"ohmydns/coremain"

	"github.com/arl/statsviz"
)

func main() {
	// Register statsviz handlers on the default serve mux.
	statsviz.RegisterDefault()
	go func() {
		http.ListenAndServe(":6080", nil)
	}()

	coremain.Run()
}
