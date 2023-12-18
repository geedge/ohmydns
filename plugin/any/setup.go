package any

import (
	"github.com/coredns/caddy"
	"ohmydns/core/dnsserver"
	"ohmydns/plugin"
)

func init() { plugin.Register("any", setup) }

func setup(c *caddy.Controller) error {
	a := Any{}

	dnsserver.GetConfig(c).AddPlugin(func(next plugin.Handler) plugin.Handler {
		a.Next = next
		return a
	})

	return nil
}
