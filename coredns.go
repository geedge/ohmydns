package main

//go:generate go run directives_generate.go

import (
	_ "ohmydns/core/plugin" // Plug in CoreDNS.
	"ohmydns/coremain"
)

func main() {
	coremain.Run()
}
