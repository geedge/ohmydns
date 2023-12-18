package local

import (
	"github.com/coredns/caddy"
	"ohmydns/core/dnsserver"
	"ohmydns/plugin"
)

func init() { plugin.Register("local", setup) }

func setup(c *caddy.Controller) error {
	l := Local{}

	dnsserver.GetConfig(c).AddPlugin(func(next plugin.Handler) plugin.Handler {
		l.Next = next
		return l
	})

	return nil
}
