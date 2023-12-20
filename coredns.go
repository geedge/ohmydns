package main

//go:generate go run directives_generate.go

import (
	"net/http"
	_ "net/http/pprof"
	_ "ohmydns/core/plugin" // Plug in CoreDNS.
	"ohmydns/coremain"
	"runtime"
)

func main() {
	runtime.GOMAXPROCS(1)
	runtime.SetMutexProfileFraction(1)
	runtime.SetBlockProfileRate(1)
	go func() {
		log.Println(http.ListenAndServe(":6061", nil))
	 }()
	coremain.Run()
}
