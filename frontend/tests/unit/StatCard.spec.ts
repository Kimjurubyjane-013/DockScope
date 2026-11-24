import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatCard from '@/components/common/StatCard.vue'

describe('StatCard', () => {
  it('renders title, value, unit, and badge correctly', () => {
    const wrapper = mount(StatCard, {
      props: {
        title: 'Total Hosts',
        value: 12,
        unit: 'hosts',
        badgeText: 'Healthy',
        status: 'success',
        subtext: 'All cluster nodes reporting',
        isPreview: true,
      },
    })

    expect(wrapper.text()).toContain('Total Hosts')
    expect(wrapper.text()).toContain('12')
    expect(wrapper.text()).toContain('hosts')
    expect(wrapper.text()).toContain('Healthy')
    expect(wrapper.text()).toContain('Preview')
    expect(wrapper.text()).toContain('All cluster nodes reporting')
  })
})
