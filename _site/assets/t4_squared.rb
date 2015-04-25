

def trans_mult(transa, transb)
  trans_ret = Array.new
  0.upto(transa.length-1) do |index|
    trans_ret.push(transa[transb[index]])
  end
  return trans_ret
end


def powers(translist)
  ret = translist.product(translist).map{|x,y| trans_mult(x,y)}  + translist
  ret.uniq
end

def pow4_size(translist)
  powers(powers(powers(powers(translist)))) #.length
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
    deg_arr.push(0)
  }
  puts("#\n")

  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|

    #pow4_size([x]).each { |y|
    a = trans_mult(x, x)
    #b = trans_mult(trans_mult(x, x),x)
    [a].each { |y|
      #strip loops
      if(node_hash[x.to_s].to_s != node_hash[y.to_s].to_s )
      print(node_hash[x.to_s].to_s + " " + node_hash[y.to_s].to_s + "\n")
      deg_arr[node_hash[y.to_s]] = deg_arr[node_hash[y.to_s]] +1
      end
    }
  }
end

print_primal_graph(4)