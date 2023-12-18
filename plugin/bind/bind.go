// Package bind allows binding to a specific interface instead of bind to all of them.
package bind

import (
	"ohmydns/plugin"
)

func init() { plugin.Register("bind", setup) }

type bind struct {
	Next   plugin.Handler
	addrs  []string
	except []string
}

// Name implements plugin.Handler.
func (b *bind) Name() string { return "bind" }
