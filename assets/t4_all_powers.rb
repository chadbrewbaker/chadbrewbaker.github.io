
def trans_mult(transa, transb)
  trans_ret = Array.new
  0.upto(transa.length-1) do |index|
    trans_ret.push(transa[transb[index]])
  end
  return trans_ret
end

def print_primal_graph(tran_size=2)
  ids =0
  deg_arr = Array.new
  node_hash = Hash.new

  counting_numbers = Enumerator.new do |yielder|
    (0..1.0/0).each do |number|
      yielder.yield number
    end
  end

  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
    node_hash[x.to_s] = ids

    puts ids.to_s + " " + x.to_s
    ids = ids +1
  }
  puts("#\n")
  edge_hash ={}

  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
    cur_t = x.dup
    orig = x.dup 
    powers_hash = {}
 
    while powers_hash[cur_t.to_s].nil?  #While I have not seen this node
      powers_hash[cur_t.to_s] = true
      old_ts = cur_t.to_s
      cur_t = trans_mult(cur_t, orig)
      s = "#{node_hash[old_ts]} #{node_hash[cur_t.to_s]}"
      edge_hash[ s ] = true
    end

  }
  edge_hash.each_key{|e|
    puts e.to_s
  }

end

print_primal_graph(4)