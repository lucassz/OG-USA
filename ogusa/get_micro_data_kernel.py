from rpcproxy.kernel import ProxyKernel
import get_micro_data


ker = ProxyKernel({'get_micro_data': get_micro_data})
ker.run()
